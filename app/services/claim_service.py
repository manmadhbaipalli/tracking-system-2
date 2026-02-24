"""
Claims processing business logic with policy linking, claim-level policy overrides, and comprehensive audit trails.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime

from app.models.claim import Claim, ClaimLevelPolicy
from app.models.policy import Policy
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimSearchRequest, ClaimStatusUpdate
from app.utils.audit import audit_log
from app.utils.exceptions import NotFoundError, ValidationError


class ClaimService:
    """Service layer for claims business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_claim(self, claim_data: ClaimCreate, user_id: UUID) -> Claim:
        """Create a new claim with policy linking and audit logging."""
        try:
            # Validate policy exists
            policy_stmt = select(Policy).where(Policy.id == claim_data.policy_id)
            policy_result = await self.db.execute(policy_stmt)
            policy = policy_result.scalar_one_or_none()

            if not policy:
                raise ValidationError("Policy not found")

            # Generate claim number if not provided
            if not claim_data.claim_number:
                claim_number = await self._generate_claim_number()
            else:
                # Check if claim number already exists
                existing_stmt = select(Claim).where(Claim.claim_number == claim_data.claim_number)
                existing_result = await self.db.execute(existing_stmt)
                if existing_result.scalar_one_or_none():
                    raise ValidationError(f"Claim number {claim_data.claim_number} already exists")
                claim_number = claim_data.claim_number

            # Create new claim
            claim = Claim(
                claim_number=claim_number,
                policy_id=claim_data.policy_id,
                date_of_loss=claim_data.date_of_loss,
                date_reported=claim_data.date_reported or datetime.utcnow().date(),
                claim_type=claim_data.claim_type,
                status=claim_data.status or "OPEN",
                description=claim_data.description,
                loss_location=claim_data.loss_location,
                adjuster_id=claim_data.adjuster_id,
                estimated_amount=claim_data.estimated_amount,
                reserve_amount=claim_data.reserve_amount,
                paid_amount=0.0,
                subrogation_referred=False,
                injury_details=claim_data.injury_details.model_dump() if claim_data.injury_details else None,
                coding_information=claim_data.coding_information.model_dump() if claim_data.coding_information else None,
                carrier_involvement=claim_data.carrier_involvement.model_dump() if claim_data.carrier_involvement else None,
                scheduled_payments=claim_data.scheduled_payments.model_dump() if claim_data.scheduled_payments else None,
                created_by=user_id,
                updated_by=user_id
            )

            self.db.add(claim)
            await self.db.commit()
            await self.db.refresh(claim)

            # Audit log
            await audit_log(
                db=self.db,
                user_id=user_id,
                action="CLAIM_CREATED",
                entity_type="Claim",
                entity_id=claim.id,
                old_values=None,
                new_values={
                    "claim_number": claim.claim_number,
                    "policy_id": str(claim.policy_id),
                    "claim_type": claim.claim_type,
                    "status": claim.status
                }
            )

            return claim

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to create claim: {str(e)}")

    async def get_claim(self, claim_id: UUID, include_policy: bool = False, include_payments: bool = False) -> Optional[Claim]:
        """Get a claim by ID with optional related data."""
        try:
            stmt = select(Claim).where(Claim.id == claim_id)

            if include_policy:
                stmt = stmt.options(selectinload(Claim.policy))
            if include_payments:
                stmt = stmt.options(selectinload(Claim.payments))

            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception:
            return None

    async def get_claim_by_number(self, claim_number: str) -> Optional[Claim]:
        """Get a claim by claim number."""
        try:
            stmt = select(Claim).where(Claim.claim_number == claim_number)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception:
            return None

    async def update_claim(self, claim_id: UUID, claim_data: ClaimUpdate, user_id: UUID) -> Claim:
        """Update a claim with audit logging."""
        try:
            # Get existing claim
            claim = await self.get_claim(claim_id)
            if not claim:
                raise NotFoundError("Claim not found")

            # Store old values for audit
            old_values = {
                "status": claim.status,
                "description": claim.description,
                "estimated_amount": str(claim.estimated_amount) if claim.estimated_amount else None,
                "reserve_amount": str(claim.reserve_amount) if claim.reserve_amount else None,
                "adjuster_id": claim.adjuster_id
            }

            # Update fields
            update_data = claim_data.model_dump(exclude_unset=True)
            new_values = {}

            for field, value in update_data.items():
                if field in ["injury_details", "coding_information", "carrier_involvement", "scheduled_payments"] and value is not None:
                    # Convert Pydantic models to dict
                    if hasattr(value, 'model_dump'):
                        value = value.model_dump()
                    setattr(claim, field, value)
                    new_values[field] = value
                elif value is not None:
                    setattr(claim, field, value)
                    new_values[field] = str(value) if isinstance(value, (int, float)) else value

            claim.updated_by = user_id

            await self.db.commit()
            await self.db.refresh(claim)

            # Audit log
            if new_values:
                await audit_log(
                    db=self.db,
                    user_id=user_id,
                    action="CLAIM_UPDATED",
                    entity_type="Claim",
                    entity_id=claim.id,
                    old_values=old_values,
                    new_values=new_values
                )

            return claim

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            raise ValidationError(f"Failed to update claim: {str(e)}")

    async def update_claim_status(self, claim_id: UUID, status_data: ClaimStatusUpdate, user_id: UUID) -> Claim:
        """Update claim status with audit logging."""
        try:
            claim = await self.get_claim(claim_id)
            if not claim:
                raise NotFoundError("Claim not found")

            old_status = claim.status
            claim.status = status_data.status
            claim.status_reason = status_data.reason
            claim.updated_by = user_id

            await self.db.commit()
            await self.db.refresh(claim)

            # Audit log
            await audit_log(
                db=self.db,
                user_id=user_id,
                action="CLAIM_STATUS_UPDATED",
                entity_type="Claim",
                entity_id=claim.id,
                old_values={"status": old_status},
                new_values={"status": status_data.status, "reason": status_data.reason}
            )

            return claim

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            raise ValidationError(f"Failed to update claim status: {str(e)}")

    async def create_claim_level_policy(self, claim_id: UUID, policy_data: Dict[str, Any], user_id: UUID) -> ClaimLevelPolicy:
        """Create claim-level policy override."""
        try:
            claim = await self.get_claim(claim_id)
            if not claim:
                raise NotFoundError("Claim not found")

            # Check if claim-level policy already exists
            existing_stmt = select(ClaimLevelPolicy).where(ClaimLevelPolicy.claim_id == claim_id)
            existing_result = await self.db.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                raise ValidationError("Claim-level policy already exists for this claim")

            claim_level_policy = ClaimLevelPolicy(
                claim_id=claim_id,
                policy_data=policy_data,
                created_by=user_id,
                updated_by=user_id
            )

            self.db.add(claim_level_policy)
            await self.db.commit()
            await self.db.refresh(claim_level_policy)

            # Audit log
            await audit_log(
                db=self.db,
                user_id=user_id,
                action="CLAIM_LEVEL_POLICY_CREATED",
                entity_type="ClaimLevelPolicy",
                entity_id=claim_level_policy.id,
                old_values=None,
                new_values={"claim_id": str(claim_id), "policy_data": policy_data}
            )

            return claim_level_policy

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            raise ValidationError(f"Failed to create claim-level policy: {str(e)}")

    async def delete_claim(self, claim_id: UUID, user_id: UUID) -> bool:
        """Soft delete a claim with audit logging."""
        try:
            claim = await self.get_claim(claim_id)
            if not claim:
                raise NotFoundError("Claim not found")

            # Check if claim has payments
            from app.models.payment import Payment
            payments_stmt = select(func.count(Payment.id)).where(Payment.claim_id == claim_id)
            payments_result = await self.db.execute(payments_stmt)
            payments_count = payments_result.scalar()

            if payments_count > 0:
                raise ValidationError("Cannot delete claim with associated payments")

            # Soft delete by setting status
            old_status = claim.status
            claim.status = "DELETED"
            claim.updated_by = user_id

            await self.db.commit()

            # Audit log
            await audit_log(
                db=self.db,
                user_id=user_id,
                action="CLAIM_DELETED",
                entity_type="Claim",
                entity_id=claim.id,
                old_values={"status": old_status},
                new_values={"status": "DELETED"}
            )

            return True

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            raise ValidationError(f"Failed to delete claim: {str(e)}")

    async def search_claims(self, search_criteria: ClaimSearchRequest) -> List[Claim]:
        """Search claims with multiple criteria."""
        try:
            stmt = select(Claim).where(Claim.status != "DELETED")

            # Apply filters
            filters = []

            if search_criteria.claim_number:
                filters.append(Claim.claim_number.ilike(f"%{search_criteria.claim_number}%"))

            if search_criteria.policy_id:
                filters.append(Claim.policy_id == search_criteria.policy_id)

            if search_criteria.date_of_loss_from:
                filters.append(Claim.date_of_loss >= search_criteria.date_of_loss_from)

            if search_criteria.date_of_loss_to:
                filters.append(Claim.date_of_loss <= search_criteria.date_of_loss_to)

            if search_criteria.claim_type:
                filters.append(Claim.claim_type == search_criteria.claim_type)

            if search_criteria.status:
                if isinstance(search_criteria.status, list):
                    filters.append(Claim.status.in_(search_criteria.status))
                else:
                    filters.append(Claim.status == search_criteria.status)

            if search_criteria.adjuster_id:
                filters.append(Claim.adjuster_id == search_criteria.adjuster_id)

            if filters:
                stmt = stmt.where(and_(*filters))

            # Apply sorting - most recent loss date first by default
            stmt = stmt.order_by(desc(Claim.date_of_loss))

            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            raise ValidationError(f"Search failed: {str(e)}")

    async def get_claim_history(self, policy_id: UUID) -> List[Claim]:
        """Get claim history for a policy, sorted by date of loss (most recent first)."""
        try:
            stmt = (
                select(Claim)
                .where(Claim.policy_id == policy_id, Claim.status != "DELETED")
                .order_by(desc(Claim.date_of_loss))
            )

            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            raise ValidationError(f"Failed to get claim history: {str(e)}")

    async def refer_to_subrogation(self, claim_id: UUID, user_id: UUID, subrogation_notes: Optional[str] = None) -> bool:
        """Refer a claim to subrogation."""
        try:
            claim = await self.get_claim(claim_id)
            if not claim:
                raise NotFoundError("Claim not found")

            if claim.subrogation_referred:
                raise ValidationError("Claim already referred to subrogation")

            old_value = claim.subrogation_referred
            claim.subrogation_referred = True
            claim.subrogation_date = datetime.utcnow().date()
            claim.subrogation_notes = subrogation_notes
            claim.updated_by = user_id

            await self.db.commit()

            # Audit log
            await audit_log(
                db=self.db,
                user_id=user_id,
                action="CLAIM_SUBROGATION_REFERRED",
                entity_type="Claim",
                entity_id=claim.id,
                old_values={"subrogation_referred": old_value},
                new_values={
                    "subrogation_referred": True,
                    "subrogation_notes": subrogation_notes
                }
            )

            return True

        except Exception as e:
            await self.db.rollback()
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            raise ValidationError(f"Failed to refer to subrogation: {str(e)}")

    async def list_claims(self, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None) -> Tuple[List[Claim], int]:
        """List claims with pagination and filtering."""
        try:
            base_where = Claim.status != "DELETED"

            if status_filter:
                base_where = and_(base_where, Claim.status == status_filter)

            # Get total count
            count_stmt = select(func.count(Claim.id)).where(base_where)
            count_result = await self.db.execute(count_stmt)
            total_count = count_result.scalar()

            # Get claims
            stmt = (
                select(Claim)
                .where(base_where)
                .order_by(desc(Claim.date_of_loss))
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            claims = result.scalars().all()

            return list(claims), total_count

        except Exception as e:
            raise ValidationError(f"Failed to list claims: {str(e)}")

    async def _generate_claim_number(self) -> str:
        """Generate a unique claim number."""
        import random
        import string

        while True:
            # Generate claim number in format CLM-YYYYMMDD-XXXX
            today = datetime.utcnow()
            date_part = today.strftime("%Y%m%d")
            random_part = ''.join(random.choices(string.digits, k=4))
            claim_number = f"CLM-{date_part}-{random_part}"

            # Check if it already exists
            existing_stmt = select(Claim).where(Claim.claim_number == claim_number)
            existing_result = await self.db.execute(existing_stmt)

            if not existing_result.scalar_one_or_none():
                return claim_number