"""
Claims Service Platform - Claim Service

Claims management service with history filtering, subrogation management,
and claim-level policy data handling.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from app.models.claim import Claim, ClaimStatus
from app.models.policy import Policy
from app.schemas.claim import ClaimCreate, ClaimUpdate
from app.core.database import get_db
from app.services.audit_service import log_action


class ClaimPolicyOverride:
    """Represents claim-level policy data overrides"""
    def __init__(self, claim_id: int, override_data: Dict[str, Any], created_by: int):
        self.claim_id = claim_id
        self.override_data = override_data
        self.created_by = created_by
        self.created_at = datetime.utcnow()


class SubrogationRecord:
    """Represents subrogation case information"""
    def __init__(self, claim_id: int, subrogation_data: Dict[str, Any]):
        self.claim_id = claim_id
        self.subrogation_data = subrogation_data
        self.status = "active"
        self.created_at = datetime.utcnow()


class SettlementCalculation:
    """Represents settlement calculation results"""
    def __init__(self, claim_id: int, settlement_amount: Decimal, calculation_details: Dict[str, Any]):
        self.claim_id = claim_id
        self.settlement_amount = settlement_amount
        self.calculation_details = calculation_details
        self.calculated_at = datetime.utcnow()


class ClaimService:
    """Claims workflow management and business logic service"""

    def __init__(self, db: Session):
        self.db = db

    async def get_claims_history(
        self,
        policy_id: Optional[int] = None,
        claim_id: Optional[int] = None,
        status_filter: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Dict[str, Any]:
        """Get claims history with status filtering and pagination"""

        try:
            # Build base query
            query = self.db.query(Claim).filter(Claim.is_deleted == False)

            # Apply filters
            if policy_id:
                query = query.filter(Claim.policy_id == policy_id)

            if claim_id:
                query = query.filter(Claim.id == claim_id)

            if status_filter:
                query = query.filter(Claim.status.in_(status_filter))

            # Get total count
            total_count = query.count()

            # Apply sorting (most recent date of loss first)
            query = query.order_by(desc(Claim.date_of_loss), desc(Claim.created_at))

            # Apply pagination
            offset = (page - 1) * page_size
            claims = query.offset(offset).limit(page_size).all()

            # Check for claim-level policy overrides
            has_claim_overrides = any(
                bool(getattr(claim, 'policy_override_data', None))
                for claim in claims
            )

            # Log access if user provided
            if user_id:
                await log_action(
                    self.db,
                    user_id,
                    "claims_history_view",
                    entity_type="claim",
                    entity_id=None,
                    details={
                        "policy_id": policy_id,
                        "status_filter": status_filter,
                        "results_count": len(claims)
                    }
                )

            # Build response
            claim_summaries = []
            for claim in claims:
                claim_data = {
                    "id": claim.id,
                    "claim_number": claim.claim_number,
                    "date_of_loss": claim.date_of_loss.isoformat() if claim.date_of_loss else None,
                    "claim_status": claim.status,
                    "claim_type": getattr(claim, 'claim_type', 'unknown'),
                    "policy_id": claim.policy_id,
                    "total_incurred": float(claim.total_incurred) if hasattr(claim, 'total_incurred') and claim.total_incurred else 0,
                    "total_paid": float(claim.total_paid) if hasattr(claim, 'total_paid') and claim.total_paid else 0,
                    "total_reserve": float(claim.total_reserve) if hasattr(claim, 'total_reserve') and claim.total_reserve else 0,
                    "has_policy_override": bool(getattr(claim, 'policy_override_data', None)),
                    "override_indicator": "Policy data modified at claim level" if getattr(claim, 'policy_override_data', None) else None,
                    "days_open": self._calculate_days_open(claim),
                    "adjuster_name": getattr(claim, 'adjuster_name', None)
                }
                claim_summaries.append(claim_data)

            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size

            return {
                "claims": claim_summaries,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_claim_overrides": has_claim_overrides,
                "filters_applied": {
                    "policy_id": policy_id,
                    "status_filter": status_filter or []
                }
            }

        except SQLAlchemyError as e:
            if user_id:
                await log_action(
                    self.db,
                    user_id,
                    "claims_history_error",
                    entity_type="claim",
                    entity_id=None,
                    details={"error": str(e)}
                )
            raise Exception(f"Database error retrieving claims: {str(e)}")
        except Exception as e:
            if user_id:
                await log_action(
                    self.db,
                    user_id,
                    "claims_history_error",
                    entity_type="claim",
                    entity_id=None,
                    details={"error": str(e)}
                )
            raise Exception(f"Failed to retrieve claims history: {str(e)}")

    async def create_claim_policy_override(
        self,
        claim_id: int,
        policy_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Create claim-level policy data override with audit trail"""

        try:
            # Verify claim exists
            claim = self.db.query(Claim).filter(
                Claim.id == claim_id,
                Claim.is_deleted == False
            ).first()

            if not claim:
                raise ValueError("Claim not found")

            # Get original policy data for comparison
            original_policy = self.db.query(Policy).filter(Policy.id == claim.policy_id).first()

            if not original_policy:
                raise ValueError("Associated policy not found")

            # Create override record
            override = ClaimPolicyOverride(
                claim_id=claim_id,
                override_data=policy_data,
                created_by=user_id
            )

            # Store override data in claim (assuming JSON field exists)
            if not hasattr(claim, 'policy_override_data'):
                # If the field doesn't exist in the model, we'll store it as metadata
                claim.metadata = claim.metadata or {}
                claim.metadata['policy_override'] = {
                    "data": policy_data,
                    "created_by": user_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "reason": "Claim-level policy data modification"
                }
            else:
                claim.policy_override_data = policy_data

            claim.updated_by = user_id
            self.db.commit()

            # Log the override creation with before/after data
            await log_action(
                self.db,
                user_id,
                "claim_policy_override_create",
                entity_type="claim",
                entity_id=claim_id,
                details={
                    "original_policy_data": original_policy.to_dict(mask_pii=True),
                    "override_data": policy_data,
                    "override_fields": list(policy_data.keys())
                }
            )

            return {
                "success": True,
                "claim_id": claim_id,
                "override_created_at": datetime.utcnow().isoformat(),
                "override_fields": list(policy_data.keys()),
                "message": "Claim-level policy data override created successfully"
            }

        except ValueError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            await log_action(
                self.db,
                user_id,
                "claim_policy_override_error",
                entity_type="claim",
                entity_id=claim_id,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to create policy override: {str(e)}")

    async def get_claim_policy_override(
        self,
        claim_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get claim-level policy data override with visual indicators"""

        try:
            claim = self.db.query(Claim).filter(
                Claim.id == claim_id,
                Claim.is_deleted == False
            ).first()

            if not claim:
                return None

            # Get override data
            override_data = None
            if hasattr(claim, 'policy_override_data') and claim.policy_override_data:
                override_data = claim.policy_override_data
            elif hasattr(claim, 'metadata') and claim.metadata and claim.metadata.get('policy_override'):
                override_data = claim.metadata['policy_override']['data']

            if not override_data:
                return None

            # Get original policy data for comparison
            original_policy = self.db.query(Policy).filter(Policy.id == claim.policy_id).first()

            # Log access
            await log_action(
                self.db,
                user_id,
                "claim_policy_override_view",
                entity_type="claim",
                entity_id=claim_id,
                details={}
            )

            return {
                "claim_id": claim_id,
                "has_override": True,
                "override_data": override_data,
                "original_policy_data": original_policy.to_dict(mask_pii=True) if original_policy else {},
                "visual_indicators": {
                    "icon": "override_warning",
                    "message": "This claim uses modified policy information",
                    "modified_fields": list(override_data.keys())
                }
            }

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "claim_policy_override_view_error",
                entity_type="claim",
                entity_id=claim_id,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to retrieve policy override: {str(e)}")

    async def manage_subrogation(
        self,
        claim_id: int,
        subrogation_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Manage subrogation workflow and tracking"""

        try:
            # Verify claim exists
            claim = self.db.query(Claim).filter(
                Claim.id == claim_id,
                Claim.is_deleted == False
            ).first()

            if not claim:
                raise ValueError("Claim not found")

            # Create subrogation record
            subrogation = SubrogationRecord(
                claim_id=claim_id,
                subrogation_data=subrogation_data
            )

            # Store subrogation data in claim metadata
            if not hasattr(claim, 'subrogation_data'):
                claim.metadata = claim.metadata or {}
                claim.metadata['subrogation'] = {
                    "status": subrogation_data.get('status', 'initiated'),
                    "responsible_party": subrogation_data.get('responsible_party'),
                    "potential_recovery": subrogation_data.get('potential_recovery', 0),
                    "attorney_assigned": subrogation_data.get('attorney_assigned'),
                    "case_number": subrogation_data.get('case_number'),
                    "initiated_date": datetime.utcnow().isoformat(),
                    "notes": subrogation_data.get('notes', '')
                }
            else:
                claim.subrogation_data = subrogation_data

            claim.updated_by = user_id
            self.db.commit()

            # Log subrogation action
            await log_action(
                self.db,
                user_id,
                "claim_subrogation_manage",
                entity_type="claim",
                entity_id=claim_id,
                details={
                    "subrogation_status": subrogation_data.get('status'),
                    "responsible_party": subrogation_data.get('responsible_party'),
                    "potential_recovery": subrogation_data.get('potential_recovery')
                }
            )

            return {
                "success": True,
                "claim_id": claim_id,
                "subrogation_status": subrogation_data.get('status', 'initiated'),
                "case_number": subrogation_data.get('case_number'),
                "message": "Subrogation case updated successfully"
            }

        except ValueError as e:
            raise e
        except Exception as e:
            self.db.rollback()
            await log_action(
                self.db,
                user_id,
                "claim_subrogation_error",
                entity_type="claim",
                entity_id=claim_id,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to manage subrogation: {str(e)}")

    async def calculate_settlement(
        self,
        claim_id: int,
        settlement_params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Calculate settlement amount based on various factors"""

        try:
            # Verify claim exists
            claim = self.db.query(Claim).filter(
                Claim.id == claim_id,
                Claim.is_deleted == False
            ).first()

            if not claim:
                raise ValueError("Claim not found")

            # Get current reserves and payments
            total_reserve = getattr(claim, 'total_reserve', Decimal('0'))
            total_paid = getattr(claim, 'total_paid', Decimal('0'))
            total_incurred = getattr(claim, 'total_incurred', Decimal('0'))

            # Settlement calculation parameters
            settlement_percentage = settlement_params.get('settlement_percentage', 100)
            discount_percentage = settlement_params.get('discount_percentage', 0)
            additional_costs = Decimal(str(settlement_params.get('additional_costs', 0)))

            # Calculate base settlement amount
            base_amount = total_incurred or total_reserve
            settlement_amount = base_amount * (Decimal(str(settlement_percentage)) / 100)

            # Apply discount if any
            if discount_percentage > 0:
                discount_amount = settlement_amount * (Decimal(str(discount_percentage)) / 100)
                settlement_amount -= discount_amount
            else:
                discount_amount = Decimal('0')

            # Add additional costs
            settlement_amount += additional_costs

            # Ensure non-negative amount
            settlement_amount = max(settlement_amount, Decimal('0'))

            # Create calculation record
            calculation = SettlementCalculation(
                claim_id=claim_id,
                settlement_amount=settlement_amount,
                calculation_details={
                    "base_amount": float(base_amount),
                    "settlement_percentage": settlement_percentage,
                    "discount_percentage": discount_percentage,
                    "discount_amount": float(discount_amount),
                    "additional_costs": float(additional_costs),
                    "final_amount": float(settlement_amount),
                    "calculation_date": datetime.utcnow().isoformat(),
                    "calculated_by": user_id
                }
            )

            # Log settlement calculation
            await log_action(
                self.db,
                user_id,
                "claim_settlement_calculate",
                entity_type="claim",
                entity_id=claim_id,
                details={
                    "base_amount": float(base_amount),
                    "settlement_amount": float(settlement_amount),
                    "settlement_percentage": settlement_percentage,
                    "discount_percentage": discount_percentage
                }
            )

            return {
                "claim_id": claim_id,
                "settlement_calculation": {
                    "base_amount": float(base_amount),
                    "settlement_percentage": settlement_percentage,
                    "discount_percentage": discount_percentage,
                    "discount_amount": float(discount_amount),
                    "additional_costs": float(additional_costs),
                    "final_settlement_amount": float(settlement_amount),
                    "total_reserve": float(total_reserve),
                    "total_paid": float(total_paid),
                    "remaining_reserve": float(max(total_reserve - settlement_amount, Decimal('0')))
                },
                "calculation_details": calculation.calculation_details,
                "calculated_at": calculation.calculated_at.isoformat()
            }

        except ValueError as e:
            raise e
        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "claim_settlement_error",
                entity_type="claim",
                entity_id=claim_id,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to calculate settlement: {str(e)}")

    async def create_claim(
        self,
        claim_data: ClaimCreate,
        user_id: int
    ) -> Dict[str, Any]:
        """Create new claim with validation"""

        try:
            # Verify policy exists
            policy = self.db.query(Policy).filter(
                Policy.id == claim_data.policy_id,
                Policy.is_deleted == False
            ).first()

            if not policy:
                raise ValueError("Associated policy not found")

            # Create claim object
            claim = Claim(**claim_data.dict(exclude_unset=True))
            claim.created_by = user_id
            claim.updated_by = user_id

            # Generate claim number if not provided
            if not claim.claim_number:
                claim.claim_number = self._generate_claim_number()

            # Set initial status if not provided
            if not claim.status:
                claim.status = ClaimStatus.OPEN.value

            self.db.add(claim)
            self.db.commit()
            self.db.refresh(claim)

            # Log creation
            await log_action(
                self.db,
                user_id,
                "claim_create",
                entity_type="claim",
                entity_id=claim.id,
                details={
                    "claim_number": claim.claim_number,
                    "policy_id": claim.policy_id
                }
            )

            return {
                "id": claim.id,
                "claim_number": claim.claim_number,
                "policy_id": claim.policy_id,
                "status": claim.status,
                "created_at": claim.created_at.isoformat()
            }

        except ValueError as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            await log_action(
                self.db,
                user_id,
                "claim_create_error",
                entity_type="claim",
                entity_id=None,
                details={"error": str(e)}
            )
            raise Exception(f"Failed to create claim: {str(e)}")

    def _calculate_days_open(self, claim: Claim) -> int:
        """Calculate number of days claim has been open"""
        if hasattr(claim, 'created_at') and claim.created_at:
            return (datetime.utcnow() - claim.created_at).days
        return 0

    def _generate_claim_number(self) -> str:
        """Generate unique claim number"""
        # Simple implementation - in production, use more sophisticated logic
        from datetime import datetime
        import random

        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = str(random.randint(1000, 9999))
        return f"CLM-{timestamp}-{random_suffix}"