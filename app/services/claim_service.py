import logging
from datetime import date, timezone, datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.claim import Claim
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimSearchParams, ClaimResponse, ClaimPolicyDataUpdate
from app.schemas.common import PageResponse
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)


async def create_claim(session: AsyncSession, data: ClaimCreate, user_id: int) -> Claim:
    """Create a new claim"""
    # Check if claim number already exists
    result = await session.execute(select(Claim).where(Claim.claim_number == data.claim_number))
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictException(f"Claim number {data.claim_number} already exists")

    # Verify policy exists
    from app.models.policy import Policy
    policy = await session.get(Policy, data.policy_id)
    if not policy:
        raise ValidationException(f"Policy with id {data.policy_id} not found")

    claim = Claim(
        claim_number=data.claim_number,
        policy_id=data.policy_id,
        loss_date=data.loss_date,
        claim_status=data.claim_status,
        description=data.description,
        claim_level_policy_data=data.claim_level_policy_data,
        injury_incident_details=data.injury_incident_details,
        coding_information=data.coding_information,
        carrier_involvement=data.carrier_involvement,
        created_by=user_id
    )
    session.add(claim)
    await session.commit()
    await session.refresh(claim)
    logger.info("Claim created: claim_id=%d, claim_number=%s, policy_id=%d, user_id=%d",
                claim.id, claim.claim_number, claim.policy_id, user_id)

    # Audit log
    await log_action(session, "claim", claim.id, "create", user_id)

    return claim


async def get_claim(session: AsyncSession, claim_id: int, user_id: int) -> Claim:
    """Get claim by ID"""
    claim = await session.get(Claim, claim_id)
    if not claim:
        raise NotFoundException(f"Claim with id {claim_id} not found")

    # Audit log for view
    await log_action(session, "claim", claim.id, "view", user_id)
    return claim


async def update_claim(session: AsyncSession, claim_id: int, data: ClaimUpdate, user_id: int) -> Claim:
    """Update claim"""
    claim = await session.get(Claim, claim_id)
    if not claim:
        raise NotFoundException(f"Claim with id {claim_id} not found")

    # Track changes for audit
    changes = {}
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            old_value = getattr(claim, field, None)
            if old_value != value:
                changes[field] = {"old": str(old_value), "new": str(value)}
                setattr(claim, field, value)

    claim.updated_by = user_id
    await session.commit()
    await session.refresh(claim)
    logger.info("Claim updated: claim_id=%d, user_id=%d", claim.id, user_id)

    # Audit log
    await log_action(session, "claim", claim.id, "update", user_id, changes)

    return claim


async def update_claim_policy_data(session: AsyncSession, claim_id: int, data: ClaimPolicyDataUpdate, user_id: int) -> Claim:
    """Update claim-level policy data (for unverified policies)"""
    claim = await session.get(Claim, claim_id)
    if not claim:
        raise NotFoundException(f"Claim with id {claim_id} not found")

    old_data = claim.claim_level_policy_data
    claim.claim_level_policy_data = data.claim_level_policy_data
    claim.updated_by = user_id

    await session.commit()
    await session.refresh(claim)
    logger.info("Claim-level policy data updated: claim_id=%d, user_id=%d", claim.id, user_id)

    # Audit log
    changes = {"claim_level_policy_data": {"old": str(old_data), "new": str(data.claim_level_policy_data)}}
    await log_action(session, "claim", claim.id, "update_policy_data", user_id, changes)

    return claim


async def refer_to_subrogation(session: AsyncSession, claim_id: int, user_id: int) -> Claim:
    """Refer claim to subrogation"""
    claim = await session.get(Claim, claim_id)
    if not claim:
        raise NotFoundException(f"Claim with id {claim_id} not found")

    if claim.referred_to_subrogation:
        raise ValidationException("Claim is already referred to subrogation")

    claim.referred_to_subrogation = True
    claim.subrogation_date = date.today()
    claim.updated_by = user_id

    await session.commit()
    await session.refresh(claim)
    logger.info("Claim referred to subrogation: claim_id=%d, user_id=%d", claim.id, user_id)

    # Audit log
    await log_action(session, "claim", claim.id, "refer_subrogation", user_id)

    return claim


async def search_claims(session: AsyncSession, params: ClaimSearchParams) -> PageResponse[ClaimResponse]:
    """Search claims with filters"""
    query = select(Claim)

    # Apply filters
    if params.claim_number:
        query = query.where(Claim.claim_number.ilike(f"%{params.claim_number}%"))
    if params.policy_id:
        query = query.where(Claim.policy_id == params.policy_id)
    if params.claim_status:
        query = query.where(Claim.claim_status == params.claim_status)
    if params.loss_date_from:
        query = query.where(Claim.loss_date >= params.loss_date_from)
    if params.loss_date_to:
        query = query.where(Claim.loss_date <= params.loss_date_to)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and sorting (most recent first)
    query = query.order_by(Claim.loss_date.desc()).offset(params.page * params.size).limit(params.size)
    result = await session.execute(query)
    claims = result.scalars().all()

    # Convert to response
    claim_responses = [ClaimResponse.model_validate(claim) for claim in claims]

    return PageResponse.create(items=claim_responses, total=total, page=params.page, size=params.size)


async def get_claims_by_policy(session: AsyncSession, policy_id: int, status_filter: str = None) -> list[ClaimResponse]:
    """Get all claims for a policy, optionally filtered by status"""
    query = select(Claim).where(Claim.policy_id == policy_id)

    if status_filter:
        query = query.where(Claim.claim_status == status_filter)

    query = query.order_by(Claim.loss_date.desc())

    result = await session.execute(query)
    claims = result.scalars().all()

    return [ClaimResponse.model_validate(claim) for claim in claims]
