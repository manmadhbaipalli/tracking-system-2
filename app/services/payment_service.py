import logging
from datetime import date
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment, PaymentDetail
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentSearchParams, PaymentResponse,
    PaymentDetailCreate, PaymentDetailResponse, PaymentVoid, PaymentReverse
)
from app.schemas.common import PageResponse
from app.security import encrypt_sensitive_data
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)


async def create_payment(session: AsyncSession, data: PaymentCreate, user_id: int) -> Payment:
    """Create a new payment"""
    # Check if payment number already exists
    result = await session.execute(select(Payment).where(Payment.payment_number == data.payment_number))
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictException(f"Payment number {data.payment_number} already exists")

    # Verify claim and policy exist
    from app.models.claim import Claim
    from app.models.policy import Policy
    claim = await session.get(Claim, data.claim_id)
    if not claim:
        raise ValidationException(f"Claim with id {data.claim_id} not found")

    policy = await session.get(Policy, data.policy_id)
    if not policy:
        raise ValidationException(f"Policy with id {data.policy_id} not found")

    # Encrypt tax_id_number if provided
    encrypted_tax_id = encrypt_sensitive_data(data.tax_id_number) if data.tax_id_number else None

    payment = Payment(
        payment_number=data.payment_number,
        claim_id=data.claim_id,
        policy_id=data.policy_id,
        payment_method=data.payment_method,
        payment_type=data.payment_type,
        total_amount=data.total_amount,
        is_eroding=data.is_eroding,
        reserve_lines=data.reserve_lines,
        is_tax_reportable=data.is_tax_reportable,
        tax_id_number=encrypted_tax_id,
        created_by=user_id
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    logger.info("Payment created: payment_id=%d, payment_number=%s, claim_id=%d, amount=%s, user_id=%d",
                payment.id, payment.payment_number, payment.claim_id, payment.total_amount, user_id)

    # Create payment details if provided
    if data.payment_details:
        for detail_data in data.payment_details:
            await add_payment_detail(session, payment.id, detail_data, user_id)

    # Audit log
    await log_action(session, "payment", payment.id, "create", user_id)

    return payment


async def get_payment(session: AsyncSession, payment_id: int, user_id: int) -> Payment:
    """Get payment by ID"""
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise NotFoundException(f"Payment with id {payment_id} not found")

    # Audit log for view
    await log_action(session, "payment", payment.id, "view", user_id)
    return payment


async def update_payment(session: AsyncSession, payment_id: int, data: PaymentUpdate, user_id: int) -> Payment:
    """Update payment"""
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise NotFoundException(f"Payment with id {payment_id} not found")

    # Can only update payments that are not issued/void/reversed
    if payment.status in ["issued", "void", "reversed"]:
        raise ValidationException(f"Cannot update payment with status {payment.status}")

    # Track changes for audit
    changes = {}
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            # Encrypt tax_id_number if being updated
            if field == "tax_id_number":
                value = encrypt_sensitive_data(value) if value else None

            old_value = getattr(payment, field, None)
            if old_value != value:
                changes[field] = {"old": str(old_value), "new": str(value)}
                setattr(payment, field, value)

    payment.updated_by = user_id
    await session.commit()
    await session.refresh(payment)
    logger.info("Payment updated: payment_id=%d, user_id=%d", payment.id, user_id)

    # Audit log
    await log_action(session, "payment", payment.id, "update", user_id, changes)

    return payment


async def void_payment(session: AsyncSession, payment_id: int, data: PaymentVoid, user_id: int) -> Payment:
    """Void a payment"""
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise NotFoundException(f"Payment with id {payment_id} not found")

    if payment.status == "void":
        raise ValidationException("Payment is already void")
    if payment.status == "reversed":
        raise ValidationException("Cannot void a reversed payment")

    payment.status = "void"
    payment.void_date = date.today()
    payment.void_reason = data.void_reason
    payment.updated_by = user_id

    await session.commit()
    await session.refresh(payment)
    logger.info("Payment voided: payment_id=%d, reason=%s, user_id=%d", payment.id, data.void_reason, user_id)

    # Audit log
    await log_action(session, "payment", payment.id, "void", user_id, {"void_reason": data.void_reason})

    return payment


async def reverse_payment(session: AsyncSession, payment_id: int, data: PaymentReverse, user_id: int) -> Payment:
    """Reverse a payment"""
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise NotFoundException(f"Payment with id {payment_id} not found")

    if payment.status == "reversed":
        raise ValidationException("Payment is already reversed")
    if payment.status == "void":
        raise ValidationException("Cannot reverse a void payment")

    payment.status = "reversed"
    payment.reversal_date = date.today()
    payment.reversal_reason = data.reversal_reason
    payment.updated_by = user_id

    await session.commit()
    await session.refresh(payment)
    logger.info("Payment reversed: payment_id=%d, reason=%s, user_id=%d", payment.id, data.reversal_reason, user_id)

    # Audit log
    await log_action(session, "payment", payment.id, "reverse", user_id, {"reversal_reason": data.reversal_reason})

    return payment


async def reissue_payment(session: AsyncSession, payment_id: int, user_id: int) -> Payment:
    """Reissue a payment (create a new payment based on original)"""
    original_payment = await session.get(Payment, payment_id)
    if not original_payment:
        raise NotFoundException(f"Payment with id {payment_id} not found")

    if original_payment.status not in ["void", "reversed"]:
        raise ValidationException("Can only reissue void or reversed payments")

    # Create new payment with same details
    new_payment_number = f"{original_payment.payment_number}-R"
    new_payment = Payment(
        payment_number=new_payment_number,
        claim_id=original_payment.claim_id,
        policy_id=original_payment.policy_id,
        payment_method=original_payment.payment_method,
        payment_type=original_payment.payment_type,
        total_amount=original_payment.total_amount,
        is_eroding=original_payment.is_eroding,
        reserve_lines=original_payment.reserve_lines,
        is_tax_reportable=original_payment.is_tax_reportable,
        tax_id_number=original_payment.tax_id_number,
        original_payment_id=original_payment.id,
        reissue_date=date.today(),
        created_by=user_id
    )
    session.add(new_payment)
    await session.commit()
    await session.refresh(new_payment)
    logger.info("Payment reissued: new_payment_id=%d, original_payment_id=%d, user_id=%d",
                new_payment.id, original_payment.id, user_id)

    # Audit log
    await log_action(session, "payment", new_payment.id, "reissue", user_id,
                    {"original_payment_id": str(original_payment.id)})

    return new_payment


async def add_payment_detail(session: AsyncSession, payment_id: int, data: PaymentDetailCreate, user_id: int) -> PaymentDetail:
    """Add a payment detail (payee) to a payment"""
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise NotFoundException(f"Payment with id {payment_id} not found")

    # Encrypt banking info if provided
    encrypted_banking = None
    if data.banking_info:
        import json
        encrypted_banking = json.loads(encrypt_sensitive_data(json.dumps(data.banking_info)))

    detail = PaymentDetail(
        payment_id=payment_id,
        payee_type=data.payee_type,
        payee_id=data.payee_id,
        payee_name=data.payee_name,
        payment_portion=data.payment_portion,
        deduction_amount=data.deduction_amount,
        deduction_reason=data.deduction_reason,
        banking_info=encrypted_banking
    )
    session.add(detail)
    await session.commit()
    await session.refresh(detail)
    logger.info("Payment detail added: detail_id=%d, payment_id=%d, payee=%s, amount=%s, user_id=%d",
                detail.id, payment_id, data.payee_name, data.payment_portion, user_id)

    return detail


async def remove_payment_detail(session: AsyncSession, detail_id: int, user_id: int):
    """Remove a payment detail"""
    detail = await session.get(PaymentDetail, detail_id)
    if not detail:
        raise NotFoundException(f"Payment detail with id {detail_id} not found")

    payment_id = detail.payment_id
    await session.delete(detail)
    await session.commit()
    logger.info("Payment detail removed: detail_id=%d, payment_id=%d, user_id=%d", detail_id, payment_id, user_id)


async def get_payment_details(session: AsyncSession, payment_id: int) -> list[PaymentDetailResponse]:
    """Get all payment details for a payment"""
    result = await session.execute(select(PaymentDetail).where(PaymentDetail.payment_id == payment_id))
    details = result.scalars().all()
    return [PaymentDetailResponse.model_validate(detail) for detail in details]


async def search_payments(session: AsyncSession, params: PaymentSearchParams) -> PageResponse[PaymentResponse]:
    """Search payments with filters"""
    query = select(Payment)

    # Apply filters
    if params.payment_number:
        query = query.where(Payment.payment_number.ilike(f"%{params.payment_number}%"))
    if params.claim_id:
        query = query.where(Payment.claim_id == params.claim_id)
    if params.policy_id:
        query = query.where(Payment.policy_id == params.policy_id)
    if params.status:
        query = query.where(Payment.status == params.status)
    if params.payment_method:
        query = query.where(Payment.payment_method == params.payment_method)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(Payment.created_at.desc()).offset(params.page * params.size).limit(params.size)
    result = await session.execute(query)
    payments = result.scalars().all()

    # Convert to response
    payment_responses = [PaymentResponse.model_validate(payment) for payment in payments]

    return PageResponse.create(items=payment_responses, total=total, page=params.page, size=params.size)
