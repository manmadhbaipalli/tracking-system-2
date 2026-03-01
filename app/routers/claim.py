from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
from app.database import get_session
from app.schemas.claim import (
    ClaimCreate, ClaimUpdate, ClaimResponse, ClaimSearchParams,
    ClaimPolicyDataUpdate, SubrogationReferral
)
from app.schemas.common import PageResponse
from app.services import claim_service
from app.security import get_current_user_id

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.post("", response_model=ClaimResponse, status_code=201)
async def create_claim(
    data: ClaimCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Create a new claim"""
    claim = await claim_service.create_claim(session, data, user_id)
    return ClaimResponse.model_validate(claim)


@router.get("/search", response_model=PageResponse[ClaimResponse])
async def search_claims(
    claim_number: Optional[str] = Query(None),
    policy_id: Optional[int] = Query(None),
    claim_status: Optional[str] = Query(None),
    loss_date_from: Optional[date] = Query(None),
    loss_date_to: Optional[date] = Query(None),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    """Search claims with filters"""
    params = ClaimSearchParams(
        claim_number=claim_number,
        policy_id=policy_id,
        claim_status=claim_status,
        loss_date_from=loss_date_from,
        loss_date_to=loss_date_to,
        page=page,
        size=size
    )
    return await claim_service.search_claims(session, params)


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get claim details"""
    claim = await claim_service.get_claim(session, claim_id, user_id)
    return ClaimResponse.model_validate(claim)


@router.put("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: int,
    data: ClaimUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Update claim"""
    claim = await claim_service.update_claim(session, claim_id, data, user_id)
    return ClaimResponse.model_validate(claim)


@router.put("/{claim_id}/policy-data", response_model=ClaimResponse)
async def update_claim_policy_data(
    claim_id: int,
    data: ClaimPolicyDataUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Update claim-level policy data (for unverified policies)"""
    claim = await claim_service.update_claim_policy_data(session, claim_id, data, user_id)
    return ClaimResponse.model_validate(claim)


@router.post("/{claim_id}/refer-subrogation", response_model=ClaimResponse)
async def refer_claim_to_subrogation(
    claim_id: int,
    data: SubrogationReferral,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Refer claim to subrogation"""
    claim = await claim_service.refer_to_subrogation(session, claim_id, user_id)
    return ClaimResponse.model_validate(claim)
