import logging
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicySearchParams, PolicyResponse
from app.schemas.common import PageResponse
from app.security import encrypt_sensitive_data, mask_ssn
from app.exceptions import NotFoundException, ConflictException
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)


async def create_policy(session: AsyncSession, data: PolicyCreate, user_id: int) -> Policy:
    """Create a new policy"""
    # Check if policy number already exists
    result = await session.execute(select(Policy).where(Policy.policy_number == data.policy_number))
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictException(f"Policy number {data.policy_number} already exists")

    # Encrypt SSN/TIN if provided
    encrypted_ssn = encrypt_sensitive_data(data.ssn_tin) if data.ssn_tin else None

    policy = Policy(
        policy_number=data.policy_number,
        insured_first_name=data.insured_first_name,
        insured_last_name=data.insured_last_name,
        organization_name=data.organization_name,
        ssn_tin=encrypted_ssn,
        policy_type=data.policy_type,
        effective_date=data.effective_date,
        expiration_date=data.expiration_date,
        status=data.status,
        vehicle_year=data.vehicle_year,
        vehicle_make=data.vehicle_make,
        vehicle_model=data.vehicle_model,
        vehicle_vin=data.vehicle_vin,
        address=data.address,
        city=data.city,
        state=data.state,
        zip=data.zip,
        coverage_types=data.coverage_types,
        coverage_limits=data.coverage_limits,
        coverage_deductibles=data.coverage_deductibles,
        created_by=user_id
    )
    session.add(policy)
    await session.commit()
    await session.refresh(policy)
    logger.info("Policy created: policy_id=%d, policy_number=%s, user_id=%d",
                policy.id, policy.policy_number, user_id)

    # Audit log
    await log_action(session, "policy", policy.id, "create", user_id)

    return policy


async def get_policy(session: AsyncSession, policy_id: int, user_id: int) -> Policy:
    """Get policy by ID"""
    policy = await session.get(Policy, policy_id)
    if not policy:
        raise NotFoundException(f"Policy with id {policy_id} not found")

    # Audit log for view
    await log_action(session, "policy", policy.id, "view", user_id)
    return policy


async def update_policy(session: AsyncSession, policy_id: int, data: PolicyUpdate, user_id: int) -> Policy:
    """Update policy"""
    policy = await session.get(Policy, policy_id)
    if not policy:
        raise NotFoundException(f"Policy with id {policy_id} not found")

    # Track changes for audit
    changes = {}
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            old_value = getattr(policy, field, None)
            if old_value != value:
                changes[field] = {"old": str(old_value), "new": str(value)}
                setattr(policy, field, value)

    policy.updated_by = user_id
    await session.commit()
    await session.refresh(policy)
    logger.info("Policy updated: policy_id=%d, user_id=%d", policy.id, user_id)

    # Audit log
    await log_action(session, "policy", policy.id, "update", user_id, changes)

    return policy


async def search_policies(session: AsyncSession, params: PolicySearchParams) -> PageResponse[PolicyResponse]:
    """Search policies with filters"""
    query = select(Policy)

    # Apply filters
    if params.policy_number:
        query = query.where(Policy.policy_number.ilike(f"%{params.policy_number}%"))
    if params.insured_first_name:
        query = query.where(Policy.insured_first_name.ilike(f"%{params.insured_first_name}%"))
    if params.insured_last_name:
        query = query.where(Policy.insured_last_name.ilike(f"%{params.insured_last_name}%"))
    if params.organization_name:
        query = query.where(Policy.organization_name.ilike(f"%{params.organization_name}%"))
    if params.policy_type:
        query = query.where(Policy.policy_type == params.policy_type)
    if params.city:
        query = query.where(Policy.city.ilike(f"%{params.city}%"))
    if params.state:
        query = query.where(Policy.state == params.state)
    if params.zip:
        query = query.where(Policy.zip.ilike(f"%{params.zip}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset(params.page * params.size).limit(params.size)
    result = await session.execute(query)
    policies = result.scalars().all()

    # Convert to response with masked SSN
    policy_responses = []
    for policy in policies:
        policy_dict = {
            **{c.name: getattr(policy, c.name) for c in policy.__table__.columns},
            "ssn_tin_masked": mask_ssn(policy.ssn_tin) if policy.ssn_tin else None
        }
        # Remove the encrypted ssn_tin from response
        policy_dict.pop("ssn_tin", None)
        policy_responses.append(PolicyResponse(**policy_dict))

    return PageResponse.create(items=policy_responses, total=total, page=params.page, size=params.size)


async def get_policy_response(policy: Policy) -> PolicyResponse:
    """Convert Policy model to PolicyResponse with masked SSN"""
    policy_dict = {
        **{c.name: getattr(policy, c.name) for c in policy.__table__.columns},
        "ssn_tin_masked": mask_ssn(policy.ssn_tin) if policy.ssn_tin else None
    }
    policy_dict.pop("ssn_tin", None)
    return PolicyResponse(**policy_dict)
