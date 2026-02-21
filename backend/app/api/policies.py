"""
Claims Service Platform - Policies API

Provides policy search, CRUD operations with proper validation and error handling.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user_token, require_permission, Permission
from app.models.policy import Policy
from app.schemas.policy import (
    PolicySearchRequest, PolicySearchResponse, PolicyCreate,
    PolicyUpdate, PolicyResponse, PolicySummary
)
from app.services.audit_service import audit_service

router = APIRouter()


@router.post("/search", response_model=PolicySearchResponse)
async def search_policies(
    search_request: PolicySearchRequest,
    current_user: dict = Depends(require_permission(Permission.POLICY_SEARCH)),
    db: Session = Depends(get_db)
):
    """Search policies with multiple criteria"""
    query = db.query(Policy).filter(Policy.is_deleted == False)

    # Apply search filters
    if search_request.policy_number:
        if search_request.search_type == "exact":
            query = query.filter(Policy.policy_number == search_request.policy_number.upper())
        else:
            query = query.filter(Policy.policy_number.ilike(f"%{search_request.policy_number}%"))

    if search_request.insured_first_name:
        query = query.filter(Policy.insured_first_name.ilike(f"%{search_request.insured_first_name}%"))

    if search_request.insured_last_name:
        query = query.filter(Policy.insured_last_name.ilike(f"%{search_request.insured_last_name}%"))

    if search_request.policy_type:
        query = query.filter(Policy.policy_type == search_request.policy_type)

    if search_request.policy_city:
        query = query.filter(Policy.city.ilike(f"%{search_request.policy_city}%"))

    if search_request.policy_state:
        query = query.filter(Policy.state == search_request.policy_state.upper())

    if search_request.policy_zip:
        query = query.filter(Policy.zip_code == search_request.policy_zip)

    # Apply date filters
    if search_request.effective_date_from:
        query = query.filter(Policy.effective_date >= search_request.effective_date_from)

    if search_request.effective_date_to:
        query = query.filter(Policy.effective_date <= search_request.effective_date_to)

    # Apply sorting
    if search_request.sort_by == "policy_number":
        sort_column = Policy.policy_number
    elif search_request.sort_by == "insured_last_name":
        sort_column = Policy.insured_last_name
    elif search_request.sort_by == "effective_date":
        sort_column = Policy.effective_date
    else:
        sort_column = Policy.created_at

    if search_request.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (search_request.page - 1) * search_request.page_size
    policies = query.offset(offset).limit(search_request.page_size).all()

    # Convert to summary objects
    policy_summaries = []
    for policy in policies:
        summary = PolicySummary(
            id=policy.id,
            policy_number=policy.policy_number,
            policy_type=policy.policy_type,
            status=policy.status,
            insured_full_name=policy.insured_full_name,
            effective_date=policy.effective_date,
            expiration_date=policy.expiration_date,
            city=policy.city,
            state=policy.state,
            is_active=policy.is_active()
        )
        policy_summaries.append(summary)

    total_pages = (total + search_request.page_size - 1) // search_request.page_size

    return PolicySearchResponse(
        policies=policy_summaries,
        total=total,
        page=search_request.page,
        page_size=search_request.page_size,
        total_pages=total_pages,
        search_criteria=search_request.dict()
    )


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: int,
    current_user: dict = Depends(require_permission(Permission.POLICY_READ)),
    db: Session = Depends(get_db)
):
    """Get policy by ID"""
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.is_deleted == False).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )

    # Convert to response model
    policy_dict = policy.to_dict(mask_pii=True)
    policy_dict['is_active'] = policy.is_active()
    policy_dict['days_until_expiration'] = policy.days_until_expiration()

    return PolicyResponse(**policy_dict)


@router.post("/", response_model=PolicyResponse)
async def create_policy(
    policy_data: PolicyCreate,
    current_user: dict = Depends(require_permission(Permission.POLICY_WRITE)),
    db: Session = Depends(get_db)
):
    """Create new policy"""
    # Check if policy number already exists
    existing = db.query(Policy).filter(Policy.policy_number == policy_data.policy_number.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy number already exists"
        )

    # Create policy
    policy = Policy(**policy_data.dict())
    policy.policy_number = policy_data.policy_number.upper()
    policy.state = policy_data.state.upper()
    policy.generate_full_name()
    policy.created_by = current_user.get("user_id")

    # Validate data
    policy.validate_data()

    db.add(policy)
    db.commit()
    db.refresh(policy)

    # Log creation
    audit_service.log_action(
        db=db,
        user_id=current_user.get("user_id"),
        action="create",
        table_name="policies",
        record_id=str(policy.id),
        new_values=policy.to_dict(),
        description=f"Created policy {policy.policy_number}"
    )

    policy_dict = policy.to_dict(mask_pii=True)
    policy_dict['is_active'] = policy.is_active()
    policy_dict['days_until_expiration'] = policy.days_until_expiration()

    return PolicyResponse(**policy_dict)