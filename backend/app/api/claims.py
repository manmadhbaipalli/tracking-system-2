"""Claims API endpoints for management and processing"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_token, require_permission, Permission
from app.models.claim import Claim
from app.models.policy import Policy
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimResponse, ClaimListResponse

router = APIRouter()


@router.post("/", response_model=ClaimResponse)
async def create_claim(
    claim_data: ClaimCreate,
    current_user: dict = Depends(require_permission(Permission.CLAIM_WRITE)),
    db: Session = Depends(get_db)
):
    """Create new claim"""
    # Verify policy exists
    policy = db.query(Policy).filter(Policy.id == claim_data.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Check claim number uniqueness
    existing = db.query(Claim).filter(Claim.claim_number == claim_data.claim_number.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Claim number already exists")

    claim = Claim(**claim_data.dict())
    claim.claim_number = claim_data.claim_number.upper()
    claim.created_by = current_user.get("user_id")
    claim.calculate_outstanding_amount()

    db.add(claim)
    db.commit()
    db.refresh(claim)

    claim_dict = claim.to_dict()
    claim_dict['days_open'] = claim.days_open()
    return ClaimResponse(**claim_dict)


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: int,
    current_user: dict = Depends(require_permission(Permission.CLAIM_READ)),
    db: Session = Depends(get_db)
):
    """Get claim by ID"""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim_dict = claim.to_dict()
    claim_dict['days_open'] = claim.days_open()
    return ClaimResponse(**claim_dict)