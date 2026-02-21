"""
Claims Service Platform - Policy Service

Advanced policy search service with exact/partial matching, SSN/TIN search optimization,
and validation business logic.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, text, desc, asc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.policy import Policy, PolicyStatus
from app.models.claim import Claim
from app.schemas.policy import PolicySearchRequest, PolicyCreate, PolicyUpdate
from app.core.database import get_db
from app.core.security import encrypt_data, decrypt_data
from app.services.audit_service import log_action
from app.utils.validators import validate_policy_number, validate_ssn, validate_tin


class PolicyService:
    """Advanced policy search and lifecycle management service"""

    def __init__(self, db: Session):
        self.db = db

    async def search_policies(
        self,
        criteria: PolicySearchRequest,
        user_id: int,
        include_deleted: bool = False
    ) -> Dict[str, Any]:
        """Advanced policy search with exact/partial matching and performance optimization"""

        try:
            # Start with base query
            query = self.db.query(Policy)

            # Apply soft delete filter
            if not include_deleted:
                query = query.filter(Policy.is_deleted == False)

            # Build search conditions based on criteria
            conditions = []

            # Policy number search
            if criteria.policy_number:
                if criteria.search_type == "exact":
                    conditions.append(Policy.policy_number == criteria.policy_number.upper())
                else:
                    conditions.append(Policy.policy_number.ilike(f"%{criteria.policy_number}%"))

            # Name searches
            if criteria.insured_first_name:
                if criteria.search_type == "exact":
                    conditions.append(Policy.insured_first_name == criteria.insured_first_name)
                else:
                    conditions.append(Policy.insured_first_name.ilike(f"%{criteria.insured_first_name}%"))

            if criteria.insured_last_name:
                if criteria.search_type == "exact":
                    conditions.append(Policy.insured_last_name == criteria.insured_last_name)
                else:
                    conditions.append(Policy.insured_last_name.ilike(f"%{criteria.insured_last_name}%"))

            # Organization name search
            if criteria.organization_name:
                if criteria.search_type == "exact":
                    conditions.append(Policy.organization_name == criteria.organization_name)
                else:
                    conditions.append(Policy.organization_name.ilike(f"%{criteria.organization_name}%"))

            # SSN/TIN search (encrypted field handling)
            if criteria.ssn_tin:
                # For encrypted fields, we need to search differently
                encrypted_ssn = encrypt_data(criteria.ssn_tin)
                conditions.append(
                    or_(
                        Policy.ssn == encrypted_ssn,
                        Policy.tin == encrypted_ssn
                    )
                )

            # Policy type
            if criteria.policy_type:
                conditions.append(Policy.policy_type == criteria.policy_type)

            # Date ranges
            if criteria.loss_date_from:
                conditions.append(Policy.loss_date >= criteria.loss_date_from)
            if criteria.loss_date_to:
                conditions.append(Policy.loss_date <= criteria.loss_date_to)

            if criteria.effective_date_from:
                conditions.append(Policy.effective_date >= criteria.effective_date_from)
            if criteria.effective_date_to:
                conditions.append(Policy.effective_date <= criteria.effective_date_to)

            # Location searches
            if criteria.policy_city:
                if criteria.search_type == "exact":
                    conditions.append(Policy.city == criteria.policy_city)
                else:
                    conditions.append(Policy.city.ilike(f"%{criteria.policy_city}%"))

            if criteria.policy_state:
                conditions.append(Policy.state == criteria.policy_state.upper())

            if criteria.policy_zip:
                conditions.append(Policy.zip_code == criteria.policy_zip)

            # Apply all conditions
            if conditions:
                query = query.filter(and_(*conditions))

            # Get total count for pagination
            total_count = query.count()

            # Apply sorting
            sort_column = getattr(Policy, criteria.sort_by, Policy.created_at)
            if criteria.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

            # Apply pagination
            offset = (criteria.page - 1) * criteria.page_size
            policies = query.offset(offset).limit(criteria.page_size).all()

            # Calculate pagination metadata
            total_pages = (total_count + criteria.page_size - 1) // criteria.page_size

            # Log search action for audit
            await log_action(
                self.db,
                user_id,
                "policy_search",
                entity_type="policy",
                entity_id=None,
                details={
                    "search_criteria": criteria.dict(),
                    "results_count": len(policies)
                }
            )

            return {
                "policies": [p.to_dict(mask_pii=True) for p in policies],
                "total": total_count,
                "page": criteria.page,
                "page_size": criteria.page_size,
                "total_pages": total_pages,
                "search_criteria": criteria.dict()
            }

        except SQLAlchemyError as e:
            # Log error
            await log_action(
                self.db,
                user_id,
                "policy_search_error",
                entity_type="policy",
                entity_id=None,
                details={"error": str(e), "criteria": criteria.dict()}
            )
            raise Exception(f"Database error during policy search: {str(e)}")
        except Exception as e:
            # Log unexpected error
            await log_action(
                self.db,
                user_id,
                "policy_search_error",
                entity_type="policy",
                entity_id=None,
                details={"error": str(e), "criteria": criteria.dict()}
            )
            raise Exception(f"Policy search failed: {str(e)}")

    async def get_policy_details(
        self,
        policy_id: int,
        user_id: int,
        mask_pii: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get detailed policy information with optional PII masking"""

        try:
            policy = self.db.query(Policy).filter(
                Policy.id == policy_id,
                Policy.is_deleted == False
            ).first()

            if not policy:
                return None

            # Log access action
            await log_action(
                self.db,
                user_id,
                "policy_view",
                entity_type="policy",
                entity_id=policy_id,
                details={"mask_pii": mask_pii}
            )

            policy_data = policy.to_dict(mask_pii=mask_pii)

            # Add calculated fields
            policy_data.update({
                "is_active": policy.is_active(),
                "is_expired": policy.is_expired(),
                "days_until_expiration": policy.days_until_expiration()
            })

            return policy_data

        except SQLAlchemyError as e:
            await log_action(
                self.db,
                user_id,
                "policy_view_error",
                entity_type="policy",
                entity_id=policy_id,
                details={"error": str(e)}
            )
            raise Exception(f"Database error retrieving policy: {str(e)}")
        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "policy_view_error",
                entity_type="policy",
                entity_id=policy_id,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to retrieve policy details: {str(e)}")

    async def create_policy(
        self,
        policy_data: PolicyCreate,
        user_id: int
    ) -> Dict[str, Any]:
        """Create new policy with validation"""

        try:
            # Validate policy data
            if policy_data.ssn:
                validate_ssn(policy_data.ssn)
            if policy_data.tin:
                validate_tin(policy_data.tin)
            validate_policy_number(policy_data.policy_number)

            # Check for duplicate policy number
            existing = self.db.query(Policy).filter(
                Policy.policy_number == policy_data.policy_number.upper(),
                Policy.is_deleted == False
            ).first()

            if existing:
                raise ValueError(f"Policy number {policy_data.policy_number} already exists")

            # Create policy object
            policy = Policy(**policy_data.dict(exclude_unset=True))
            policy.created_by = user_id
            policy.updated_by = user_id

            # Generate full name
            policy.generate_full_name()

            # Update search vector
            policy.update_search_vector()

            # Save to database
            self.db.add(policy)
            self.db.commit()
            self.db.refresh(policy)

            # Log creation
            await log_action(
                self.db,
                user_id,
                "policy_create",
                entity_type="policy",
                entity_id=policy.id,
                details={"policy_number": policy.policy_number}
            )

            return policy.to_dict(mask_pii=True)

        except IntegrityError as e:
            self.db.rollback()
            if "policy_number" in str(e):
                raise ValueError("Policy number already exists")
            raise Exception(f"Database integrity error: {str(e)}")
        except ValueError as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            await log_action(
                self.db,
                user_id,
                "policy_create_error",
                entity_type="policy",
                entity_id=None,
                details={"error": str(e), "policy_number": policy_data.policy_number}
            )
            raise Exception(f"Failed to create policy: {str(e)}")

    async def update_policy(
        self,
        policy_id: int,
        policy_data: PolicyUpdate,
        user_id: int
    ) -> Dict[str, Any]:
        """Update existing policy"""

        try:
            policy = self.db.query(Policy).filter(
                Policy.id == policy_id,
                Policy.is_deleted == False
            ).first()

            if not policy:
                raise ValueError("Policy not found")

            # Update fields
            update_data = policy_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(policy, field, value)

            policy.updated_by = user_id

            # Regenerate full name if name fields changed
            if any(field in update_data for field in ['insured_first_name', 'insured_last_name', 'organization_name']):
                policy.generate_full_name()

            # Update search vector
            policy.update_search_vector()

            self.db.commit()

            # Log update
            await log_action(
                self.db,
                user_id,
                "policy_update",
                entity_type="policy",
                entity_id=policy_id,
                details={"updated_fields": list(update_data.keys())}
            )

            return policy.to_dict(mask_pii=True)

        except ValueError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            await log_action(
                self.db,
                user_id,
                "policy_update_error",
                entity_type="policy",
                entity_id=policy_id,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to update policy: {str(e)}")

    async def get_policy_claims_history(
        self,
        policy_id: int,
        user_id: int,
        status_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get claims history for a policy with optional status filtering"""

        try:
            # Verify policy exists
            policy = self.db.query(Policy).filter(
                Policy.id == policy_id,
                Policy.is_deleted == False
            ).first()

            if not policy:
                raise ValueError("Policy not found")

            # Build claims query
            query = self.db.query(Claim).filter(
                Claim.policy_id == policy_id,
                Claim.is_deleted == False
            )

            # Apply status filter if provided
            if status_filter:
                query = query.filter(Claim.status.in_(status_filter))

            # Order by date of loss (most recent first)
            claims = query.order_by(desc(Claim.date_of_loss)).all()

            # Calculate summary statistics
            total_claims = len(claims)
            open_claims = len([c for c in claims if c.status in ['open', 'investigating', 'pending']])

            # Log access
            await log_action(
                self.db,
                user_id,
                "policy_claims_view",
                entity_type="policy",
                entity_id=policy_id,
                details={
                    "status_filter": status_filter,
                    "claims_count": total_claims
                }
            )

            return {
                "policy_id": policy_id,
                "claims": [
                    {
                        "id": claim.id,
                        "claim_number": claim.claim_number,
                        "date_of_loss": claim.date_of_loss.isoformat() if claim.date_of_loss else None,
                        "status": claim.status,
                        "claim_type": claim.claim_type,
                        "total_incurred": float(claim.total_incurred) if claim.total_incurred else 0,
                        "total_paid": float(claim.total_paid) if claim.total_paid else 0,
                        "days_open": claim.days_open() if hasattr(claim, 'days_open') else 0,
                        "has_policy_override": bool(getattr(claim, 'policy_override_data', None))
                    }
                    for claim in claims
                ],
                "total_claims": total_claims,
                "open_claims": open_claims,
                "status_filter": status_filter or []
            }

        except ValueError as e:
            raise e
        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "policy_claims_view_error",
                entity_type="policy",
                entity_id=policy_id,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to retrieve policy claims: {str(e)}")

    async def validate_policy_data(
        self,
        policy_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Validate policy data and return validation results"""

        try:
            errors = []
            warnings = []

            # Check required fields
            required_fields = [
                'policy_number', 'policy_type', 'effective_date', 'expiration_date',
                'insured_first_name', 'insured_last_name', 'address_line1', 'city', 'state', 'zip_code'
            ]

            for field in required_fields:
                if not policy_data.get(field):
                    errors.append(f"{field} is required")

            # Validate policy number format
            if policy_data.get('policy_number'):
                try:
                    validate_policy_number(policy_data['policy_number'])
                except ValueError as e:
                    errors.append(f"Invalid policy number: {str(e)}")

            # Validate SSN/TIN if provided
            if policy_data.get('ssn'):
                try:
                    validate_ssn(policy_data['ssn'])
                except ValueError as e:
                    errors.append(f"Invalid SSN: {str(e)}")

            if policy_data.get('tin'):
                try:
                    validate_tin(policy_data['tin'])
                except ValueError as e:
                    errors.append(f"Invalid TIN: {str(e)}")

            # Validate dates
            if policy_data.get('effective_date') and policy_data.get('expiration_date'):
                try:
                    eff_date = date.fromisoformat(policy_data['effective_date'])
                    exp_date = date.fromisoformat(policy_data['expiration_date'])
                    if eff_date >= exp_date:
                        errors.append("Effective date must be before expiration date")
                except ValueError:
                    errors.append("Invalid date format")

            # Check for duplicate policy number
            if policy_data.get('policy_number'):
                existing = self.db.query(Policy).filter(
                    Policy.policy_number == policy_data['policy_number'].upper(),
                    Policy.is_deleted == False
                ).first()
                if existing:
                    errors.append("Policy number already exists")

            # Business rule warnings
            if policy_data.get('policy_type') == 'auto' and not policy_data.get('vehicle_vin'):
                warnings.append("VIN is recommended for auto policies")

            if policy_data.get('premium_amount') and float(policy_data['premium_amount']) <= 0:
                warnings.append("Premium amount should be greater than zero")

            # Log validation action
            await log_action(
                self.db,
                user_id,
                "policy_validate",
                entity_type="policy",
                entity_id=None,
                details={
                    "policy_number": policy_data.get('policy_number'),
                    "errors_count": len(errors),
                    "warnings_count": len(warnings)
                }
            )

            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "policy_validate_error",
                entity_type="policy",
                entity_id=None,
                details={"error": str(e)}
            )
            raise Exception(f"Policy validation failed: {str(e)}")

    async def update_search_vectors(self, policy: Policy) -> None:
        """Update search vector for full-text search optimization"""

        try:
            policy.update_search_vector()
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update search vectors: {str(e)}")

    async def bulk_update_search_vectors(self, user_id: int) -> Dict[str, Any]:
        """Bulk update search vectors for all policies"""

        try:
            policies = self.db.query(Policy).filter(Policy.is_deleted == False).all()
            updated_count = 0

            for policy in policies:
                policy.update_search_vector()
                updated_count += 1

            self.db.commit()

            # Log bulk operation
            await log_action(
                self.db,
                user_id,
                "policy_bulk_search_update",
                entity_type="policy",
                entity_id=None,
                details={"updated_count": updated_count}
            )

            return {
                "success": True,
                "updated_count": updated_count,
                "message": f"Updated search vectors for {updated_count} policies"
            }

        except Exception as e:
            self.db.rollback()
            await log_action(
                self.db,
                user_id,
                "policy_bulk_search_update_error",
                entity_type="policy",
                entity_id=None,
                details={"error": str(e)}
            )
            raise Exception(f"Bulk search vector update failed: {str(e)}")