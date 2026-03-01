from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_session
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyResponse, PolicySearchParams
from app.schemas.claim import ClaimResponse
from app.schemas.common import PageResponse
from app.services import policy_service, claim_service
from app.security import get_current_user_id

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(
    data: PolicyCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Create a new policy"""
    policy = await policy_service.create_policy(session, data, user_id)
    return await policy_service.get_policy_response(policy)


@router.get("/search", response_model=PageResponse[PolicyResponse])
async def search_policies(
    policy_number: Optional[str] = Query(None),
    insured_first_name: Optional[str] = Query(None),
    insured_last_name: Optional[str] = Query(None),
    organization_name: Optional[str] = Query(None),
    policy_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    zip: Optional[str] = Query(None),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    """Search policies with filters"""
    params = PolicySearchParams(
        policy_number=policy_number,
        insured_first_name=insured_first_name,
        insured_last_name=insured_last_name,
        organization_name=organization_name,
        policy_type=policy_type,
        city=city,
        state=state,
        zip=zip,
        page=page,
        size=size
    )
    return await policy_service.search_policies(session, params)


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get policy details"""
    policy = await policy_service.get_policy(session, policy_id, user_id)
    return await policy_service.get_policy_response(policy)


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: int,
    data: PolicyUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Update policy"""
    policy = await policy_service.update_policy(session, policy_id, data, user_id)
    return await policy_service.get_policy_response(policy)


@router.get("/{policy_id}/claims", response_model=list[ClaimResponse])
async def get_policy_claims(
    policy_id: int,
    status: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get claim history for a policy"""
    return await claim_service.get_claims_by_policy(session, policy_id, status)
