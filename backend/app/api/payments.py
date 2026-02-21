"""Payment processing REST API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_permission, Permission
from app.models.payment import Payment
from app.models.claim import Claim
from app.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter()


@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: dict = Depends(require_permission(Permission.PAYMENT_CREATE)),
    db: Session = Depends(get_db)
):
    """Create payment"""
    # Verify claim exists
    claim = db.query(Claim).filter(Claim.id == payment_data.claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    payment = Payment(**payment_data.dict())
    payment.policy_id = claim.policy_id
    payment.created_by = current_user.get("user_id")
    payment.generate_payment_number()
    payment.validate_data()

    db.add(payment)
    db.commit()
    db.refresh(payment)

    payment_dict = payment.to_dict(mask_sensitive=True)
    payment_dict['net_amount'] = float(payment.calculate_net_amount())
    return PaymentResponse(**payment_dict)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: dict = Depends(require_permission(Permission.PAYMENT_READ)),
    db: Session = Depends(get_db)
):
    """Get payment by ID"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment_dict = payment.to_dict(mask_sensitive=True)
    payment_dict['net_amount'] = float(payment.calculate_net_amount())
    return PaymentResponse(**payment_dict)