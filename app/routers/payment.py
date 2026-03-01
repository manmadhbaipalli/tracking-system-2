from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_session
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentSearchParams,
    PaymentDetailCreate, PaymentDetailResponse,
    PaymentVoid, PaymentReverse, PaymentReissue
)
from app.schemas.common import PageResponse
from app.services import payment_service
from app.security import get_current_user_id

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=201)
async def create_payment(
    data: PaymentCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Create a new payment"""
    payment = await payment_service.create_payment(session, data, user_id)
    return PaymentResponse.model_validate(payment)


@router.get("/search", response_model=PageResponse[PaymentResponse])
async def search_payments(
    payment_number: Optional[str] = Query(None),
    claim_id: Optional[int] = Query(None),
    policy_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    """Search payments with filters"""
    params = PaymentSearchParams(
        payment_number=payment_number,
        claim_id=claim_id,
        policy_id=policy_id,
        status=status,
        payment_method=payment_method,
        page=page,
        size=size
    )
    return await payment_service.search_payments(session, params)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get payment details"""
    payment = await payment_service.get_payment(session, payment_id, user_id)
    return PaymentResponse.model_validate(payment)


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Update payment"""
    payment = await payment_service.update_payment(session, payment_id, data, user_id)
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/void", response_model=PaymentResponse)
async def void_payment(
    payment_id: int,
    data: PaymentVoid,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Void a payment"""
    payment = await payment_service.void_payment(session, payment_id, data, user_id)
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/reverse", response_model=PaymentResponse)
async def reverse_payment(
    payment_id: int,
    data: PaymentReverse,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Reverse a payment"""
    payment = await payment_service.reverse_payment(session, payment_id, data, user_id)
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/reissue", response_model=PaymentResponse)
async def reissue_payment(
    payment_id: int,
    data: PaymentReissue,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Reissue a payment"""
    payment = await payment_service.reissue_payment(session, payment_id, user_id)
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/details", response_model=PaymentDetailResponse, status_code=201)
async def add_payment_detail(
    payment_id: int,
    data: PaymentDetailCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Add a payment detail (payee) to a payment"""
    detail = await payment_service.add_payment_detail(session, payment_id, data, user_id)
    return PaymentDetailResponse.model_validate(detail)


@router.delete("/{payment_id}/details/{detail_id}", status_code=204)
async def remove_payment_detail(
    payment_id: int,
    detail_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Remove a payment detail"""
    await payment_service.remove_payment_detail(session, detail_id, user_id)


@router.get("/{payment_id}/details", response_model=list[PaymentDetailResponse])
async def get_payment_details(
    payment_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get all payment details for a payment"""
    return await payment_service.get_payment_details(session, payment_id)
