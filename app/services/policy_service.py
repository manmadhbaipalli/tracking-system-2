"""
Policy business logic with advanced search algorithms, audit logging, and performance optimization.
"""

import time
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicySearchRequest, PolicySearchResponse, PolicyResponse
from app.utils.security import encrypt_data, hash_ssn_tin, mask_ssn_tin
from app.utils.audit import audit_log
from app.utils.exceptions import NotFoundError, ValidationError


class PolicyService:
    """Service layer for policy business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_policy(self, policy_data: PolicyCreate, user_id: UUID) -> Policy:
        """Create a new policy with audit logging."""
        try:
            # Check if policy number already exists
            existing_stmt = select(Policy).where(Policy.policy_number == policy_data.policy_number)
            existing_result = await self.db.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                raise ValidationError(f"Policy number {policy_data.policy_number} already exists")

            # Prepare SSN/TIN encryption and hashing if provided
            ssn_tin_encrypted = None
            ssn_tin_hash = None
            if policy_data.ssn_tin:
                ssn_tin_encrypted = encrypt_data(policy_data.ssn_tin)
                ssn_tin_hash = hash_ssn_tin(policy_data.ssn_tin)

            # Convert schemas to dict for JSON fields
            vehicle_details = policy_data.vehicle_details.model_dump() if policy_data.vehicle_details else None
            coverage_details = policy_data.coverage_details.model_dump() if policy_data.coverage_details else None

            # Create new policy
            policy = Policy(
                policy_number=policy_data.policy_number,
                policy_type=policy_data.policy_type,
                policy_status="ACTIVE",
                effective_date=policy_data.effective_date,
                expiration_date=policy_data.expiration_date,
                insured_first_name=policy_data.insured_first_name,
                insured_last_name=policy_data.insured_last_name,
                organizational_name=policy_data.organizational_name,
                ssn_tin_encrypted=ssn_tin_encrypted,
                ssn_tin_hash=ssn_tin_hash,
                policy_address=policy_data.policy_address,
                policy_city=policy_data.policy_city,
                policy_state=policy_data.policy_state.upper(),
                policy_zip=policy_data.policy_zip,
                vehicle_details=vehicle_details,
                coverage_details=coverage_details,
                premium_amount=policy_data.premium_amount,
                deductible_amount=policy_data.deductible_amount,
                agent_id=policy_data.agent_id,
                underwriter=policy_data.underwriter,
                notes=policy_data.notes,
                created_by=user_id,
                updated_by=user_id
            )

            self.db.add(policy)
            await self.db.commit()
            await self.db.refresh(policy)

            # Audit log
            await audit_log(
                db=self.db,
                user_id=user_id,
                action="POLICY_CREATED",
                entity_type="Policy",
                entity_id=policy.id,
                old_values=None,
                new_values={"policy_number": policy.policy_number, "policy_type": policy.policy_type}
            )

            return policy

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to create policy: {str(e)}")

    async def get_policy(self, policy_id: UUID, include_claims: bool = False) -> Optional[Policy]:
        """Get a policy by ID with optional claims."""
        try:
            stmt = select(Policy).where(Policy.id == policy_id)

            if include_claims:
                stmt = stmt.options(selectinload(Policy.claims))

            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception:
            return None

    async def get_policy_by_number(self, policy_number: str) -> Optional[Policy]:
        """Get a policy by policy number."""
        try:
            stmt = select(Policy).where(Policy.policy_number == policy_number)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception:
            return None

    async def update_policy(self, policy_id: UUID, policy_data: PolicyUpdate, user_id: UUID) -> Policy:
        """Update a policy with audit logging."""
        try:
            # Get existing policy
            policy = await self.get_policy(policy_id)
            if not policy:
                raise NotFoundError("Policy not found")

            # Store old values for audit
            old_values = {
                "policy_type": policy.policy_type,
                "policy_status": policy.policy_status,
                "insured_first_name": policy.insured_first_name,
                "insured_last_name": policy.insured_last_name,
                "policy_city": policy.policy_city,
                "policy_state": policy.policy_state,
                "policy_zip": policy.policy_zip
            }

            # Update fields
            update_data = policy_data.model_dump(exclude_unset=True)
            new_values = {}

            for field, value in update_data.items():
                if field in ["vehicle_details", "coverage_details"] and value is not None:
                    # Convert Pydantic models to dict
                    if hasattr(value, 'model_dump'):
                        value = value.model_dump()
                    setattr(policy, field, value)
                    new_values[field] = value
                elif field == "policy_state" and value is not None:
                    setattr(policy, field, value.upper())
                    new_values[field] = value.upper()
                elif value is not None:
                    setattr(policy, field, value)
                    new_values[field] = value

            policy.updated_by = user_id

            await self.db.commit()
            await self.db.refresh(policy)

            # Audit log
            if new_values:
                await audit_log(
                    db=self.db,
                    user_id=user_id,
                    action="POLICY_UPDATED",
                    entity_type="Policy",
                    entity_id=policy.id,
                    old_values=old_values,
                    new_values=new_values
                )

            return policy

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            raise ValidationError(f"Failed to update policy: {str(e)}")

    async def delete_policy(self, policy_id: UUID, user_id: UUID) -> bool:
        """Soft delete a policy with audit logging."""
        try:
            policy = await self.get_policy(policy_id)
            if not policy:
                raise NotFoundError("Policy not found")

            # Check if policy has active claims
            from app.models.claim import Claim
            claims_stmt = select(func.count(Claim.id)).where(
                Claim.policy_id == policy_id,
                Claim.status.in_(["OPEN", "IN_PROGRESS"])
            )
            claims_result = await self.db.execute(claims_stmt)
            active_claims_count = claims_result.scalar()

            if active_claims_count > 0:
                raise ValidationError("Cannot delete policy with active claims")

            # Soft delete by setting status
            old_status = policy.policy_status
            policy.policy_status = "DELETED"
            policy.updated_by = user_id

            await self.db.commit()

            # Audit log
            await audit_log(
                db=self.db,
                user_id=user_id,
                action="POLICY_DELETED",
                entity_type="Policy",
                entity_id=policy.id,
                old_values={"policy_status": old_status},
                new_values={"policy_status": "DELETED"}
            )

            return True

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            raise ValidationError(f"Failed to delete policy: {str(e)}")

    async def search_policies(self, search_criteria: PolicySearchRequest, user_id: UUID) -> PolicySearchResponse:
        """Advanced policy search with multiple criteria and performance tracking."""
        start_time = time.time()

        try:
            # Build base query
            stmt = select(Policy).where(Policy.policy_status != "DELETED")

            # Apply search filters
            filters = []

            if search_criteria.policy_number:
                if len(search_criteria.policy_number) >= 3:
                    filters.append(Policy.policy_number.ilike(f"%{search_criteria.policy_number}%"))
                else:
                    filters.append(Policy.policy_number == search_criteria.policy_number)

            if search_criteria.insured_first_name:
                filters.append(Policy.insured_first_name.ilike(f"%{search_criteria.insured_first_name}%"))

            if search_criteria.insured_last_name:
                filters.append(Policy.insured_last_name.ilike(f"%{search_criteria.insured_last_name}%"))

            if search_criteria.policy_type:
                filters.append(Policy.policy_type == search_criteria.policy_type)

            if search_criteria.loss_date:
                filters.append(Policy.loss_date == search_criteria.loss_date)

            if search_criteria.policy_city:
                filters.append(Policy.policy_city.ilike(f"%{search_criteria.policy_city}%"))

            if search_criteria.policy_state:
                filters.append(Policy.policy_state == search_criteria.policy_state.upper())

            if search_criteria.policy_zip:
                filters.append(Policy.policy_zip.ilike(f"%{search_criteria.policy_zip}%"))

            if search_criteria.organizational_name:
                filters.append(Policy.organizational_name.ilike(f"%{search_criteria.organizational_name}%"))

            if search_criteria.ssn_tin:
                # Hash the provided SSN/TIN for comparison
                ssn_tin_hash = hash_ssn_tin(search_criteria.ssn_tin)
                filters.append(Policy.ssn_tin_hash == ssn_tin_hash)

            if filters:
                stmt = stmt.where(and_(*filters))

            # Get total count for pagination
            count_stmt = select(func.count(Policy.id)).where(stmt.whereclause)
            count_result = await self.db.execute(count_stmt)
            total_count = count_result.scalar()

            # Apply sorting
            if search_criteria.sort_by == "policy_number":
                sort_col = Policy.policy_number
            elif search_criteria.sort_by == "insured_name":
                sort_col = Policy.insured_last_name
            elif search_criteria.sort_by == "effective_date":
                sort_col = Policy.effective_date
            elif search_criteria.sort_by == "expiration_date":
                sort_col = Policy.expiration_date
            else:
                sort_col = Policy.policy_number

            if search_criteria.sort_order == "desc":
                stmt = stmt.order_by(desc(sort_col))
            else:
                stmt = stmt.order_by(asc(sort_col))

            # Apply pagination
            offset = (search_criteria.page - 1) * search_criteria.limit
            stmt = stmt.offset(offset).limit(search_criteria.limit)

            # Execute search
            result = await self.db.execute(stmt)
            policies = result.scalars().all()

            # Convert to response format
            policy_responses = []
            for policy in policies:
                policy_response = PolicyResponse(
                    id=policy.id,
                    policy_number=policy.policy_number,
                    policy_type=policy.policy_type,
                    policy_status=policy.policy_status,
                    effective_date=policy.effective_date,
                    expiration_date=policy.expiration_date,
                    insured_name=policy.insured_name,
                    organizational_name=policy.organizational_name,
                    ssn_tin_masked=mask_ssn_tin(policy.ssn_tin_encrypted) if policy.ssn_tin_encrypted else None,
                    policy_address=policy.policy_address,
                    policy_city=policy.policy_city,
                    policy_state=policy.policy_state,
                    policy_zip=policy.policy_zip,
                    full_address=policy.full_address,
                    vehicle_details=policy.vehicle_details,
                    coverage_details=policy.coverage_details,
                    premium_amount=policy.premium_amount,
                    deductible_amount=policy.deductible_amount,
                    agent_id=policy.agent_id,
                    underwriter=policy.underwriter,
                    is_active=policy.is_active,
                    is_expired=policy.is_expired,
                    days_until_expiration=policy.days_until_expiration(),
                    created_at=policy.created_at,
                    updated_at=policy.updated_at
                )
                policy_responses.append(policy_response)

            # Calculate search time
            search_time_ms = int((time.time() - start_time) * 1000)

            # Audit search
            await audit_log(
                db=self.db,
                user_id=user_id,
                action="POLICY_SEARCH",
                entity_type="Policy",
                entity_id=None,
                old_values=None,
                new_values={
                    "search_criteria": search_criteria.model_dump(exclude_unset=True),
                    "results_count": len(policy_responses),
                    "search_time_ms": search_time_ms
                }
            )

            return PolicySearchResponse(
                items=policy_responses,
                total_count=total_count,
                page=search_criteria.page,
                limit=search_criteria.limit,
                has_next=(search_criteria.page * search_criteria.limit) < total_count,
                has_previous=search_criteria.page > 1,
                search_time_ms=search_time_ms
            )

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Search failed: {str(e)}")

    async def list_policies(self, skip: int = 0, limit: int = 100) -> Tuple[List[Policy], int]:
        """List policies with pagination."""
        try:
            # Get total count
            count_stmt = select(func.count(Policy.id)).where(Policy.policy_status != "DELETED")
            count_result = await self.db.execute(count_stmt)
            total_count = count_result.scalar()

            # Get policies
            stmt = (
                select(Policy)
                .where(Policy.policy_status != "DELETED")
                .order_by(desc(Policy.created_at))
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            policies = result.scalars().all()

            return list(policies), total_count

        except Exception as e:
            raise ValidationError(f"Failed to list policies: {str(e)}")