"""
Claims Service Platform - Claim Model

Claims entity with policy relationships, claim-level policy data, and status tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Decimal, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

from app.core.database import Base, EncryptedString
from app.utils.validators import validate_claim_number


class ClaimStatus(enum.Enum):
    """Claim status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    PAID = "paid"
    DENIED = "denied"
    PENDING = "pending"
    INVESTIGATION = "investigation"
    SETTLEMENT = "settlement"
    LITIGATION = "litigation"


class ClaimType(enum.Enum):
    """Claim type enumeration"""
    AUTO_LIABILITY = "auto_liability"
    AUTO_COLLISION = "auto_collision"
    AUTO_COMPREHENSIVE = "auto_comprehensive"
    PROPERTY_DAMAGE = "property_damage"
    BODILY_INJURY = "bodily_injury"
    PERSONAL_INJURY = "personal_injury"
    THEFT = "theft"
    FIRE = "fire"
    WATER_DAMAGE = "water_damage"
    WINDSTORM = "windstorm"
    WORKERS_COMP = "workers_comp"
    MEDICAL = "medical"
    LIABILITY = "liability"


class ClaimSeverity(enum.Enum):
    """Claim severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CATASTROPHIC = "catastrophic"


class Claim(Base):
    """Claims model with policy relationships and claim-level policy data"""

    __tablename__ = "claims"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Claim identification
    claim_number = Column(String(25), unique=True, nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False, index=True)

    # Claim basics
    claim_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=ClaimStatus.OPEN.value, index=True)
    severity = Column(String(20), default=ClaimSeverity.LOW.value)

    # Important dates
    date_of_loss = Column(Date, nullable=False, index=True)
    date_reported = Column(Date, nullable=False, index=True)
    date_closed = Column(Date, index=True)

    # Loss details
    loss_description = Column(Text, nullable=False)
    loss_cause = Column(String(100))
    loss_location = Column(String(500))
    police_report_number = Column(String(50))

    # Financial information
    reserve_amount = Column(Decimal(12, 2), default=0)
    paid_amount = Column(Decimal(12, 2), default=0)
    recovery_amount = Column(Decimal(12, 2), default=0)
    outstanding_amount = Column(Decimal(12, 2), default=0)

    # Reserve lines (JSON array of reserve allocations)
    reserve_lines = Column(JSON)

    # Claim handlers and assignment
    adjuster_id = Column(Integer, ForeignKey("users.id"))
    adjuster_name = Column(String(100))
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    external_adjuster = Column(String(100))

    # Coverage information
    coverage_type = Column(String(50))
    policy_limit = Column(Decimal(12, 2))
    deductible = Column(Decimal(10, 2))

    # Liability and fault
    fault_percentage = Column(Decimal(5, 2))  # 0.00 to 100.00
    liable_party = Column(String(200))
    comparative_fault = Column(JSON)  # Array of fault allocations

    # Parties involved
    claimant_name = Column(String(200))
    claimant_contact = Column(JSON)  # Contact details
    insured_contact = Column(JSON)   # Insured contact at time of claim

    # Claim-level policy data override (visual indicator flag)
    has_claim_level_policy_data = Column(Boolean, default=False)
    claim_policy_data = Column(JSON)  # Override policy data specific to this claim

    # Investigation and documentation
    investigation_notes = Column(Text)
    documentation_status = Column(String(50), default="incomplete")
    witness_statements = Column(JSON)  # Array of witness information
    expert_reports = Column(JSON)     # Array of expert report references

    # Settlement and negotiation
    demand_amount = Column(Decimal(12, 2))
    settlement_amount = Column(Decimal(12, 2))
    settlement_date = Column(Date)
    settlement_terms = Column(Text)

    # Subrogation
    subrogation_potential = Column(Boolean, default=False)
    subrogation_amount = Column(Decimal(12, 2))
    subrogation_status = Column(String(50))

    # Litigation tracking
    litigation_status = Column(String(50))
    attorney_name = Column(String(100))
    court_case_number = Column(String(100))

    # Medical information (for injury claims)
    medical_providers = Column(JSON)  # Array of medical provider info
    injury_details = Column(JSON)     # Injury classifications and details
    treatment_status = Column(String(50))

    # Vehicle information (for auto claims)
    vehicle_damage_description = Column(Text)
    vehicle_repairable = Column(Boolean)
    total_loss = Column(Boolean, default=False)
    salvage_value = Column(Decimal(10, 2))

    # Property information (for property claims)
    property_damage_description = Column(Text)
    temporary_repairs_needed = Column(Boolean, default=False)
    additional_living_expenses = Column(Decimal(10, 2))

    # Compliance and regulatory
    regulatory_reporting_required = Column(Boolean, default=False)
    regulatory_report_date = Column(Date)

    # Workflow and approval
    requires_supervisor_approval = Column(Boolean, default=False)
    supervisor_approved = Column(Boolean, default=False)
    approval_date = Column(DateTime(timezone=True))
    approval_notes = Column(Text)

    # Notifications and communications
    notifications_sent = Column(JSON)  # Array of notification records
    communication_log = Column(JSON)   # Communication history

    # Performance metrics
    first_contact_date = Column(Date)
    resolution_target_date = Column(Date)
    cycle_time_days = Column(Integer)

    # Audit and tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer, ForeignKey("users.id"))

    # Search optimization
    search_vector = Column(Text)

    # Relationships
    policy = relationship("Policy", back_populates="claims")
    payments = relationship("Payment", back_populates="claim")

    adjuster = relationship("User", foreign_keys=[adjuster_id])
    supervisor = relationship("User", foreign_keys=[supervisor_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    def __repr__(self):
        return f"<Claim(id={self.id}, claim_number='{self.claim_number}', status='{self.status}')>"

    def to_dict(self, include_policy_data: bool = False):
        """Convert claim to dictionary"""
        data = {
            "id": self.id,
            "claim_number": self.claim_number,
            "policy_id": self.policy_id,
            "claim_type": self.claim_type,
            "status": self.status,
            "severity": self.severity,
            "date_of_loss": self.date_of_loss.isoformat() if self.date_of_loss else None,
            "date_reported": self.date_reported.isoformat() if self.date_reported else None,
            "date_closed": self.date_closed.isoformat() if self.date_closed else None,
            "loss_description": self.loss_description,
            "loss_cause": self.loss_cause,
            "loss_location": self.loss_location,
            "police_report_number": self.police_report_number,
            "reserve_amount": float(self.reserve_amount) if self.reserve_amount else 0,
            "paid_amount": float(self.paid_amount) if self.paid_amount else 0,
            "recovery_amount": float(self.recovery_amount) if self.recovery_amount else 0,
            "outstanding_amount": float(self.outstanding_amount) if self.outstanding_amount else 0,
            "reserve_lines": self.reserve_lines,
            "adjuster_id": self.adjuster_id,
            "adjuster_name": self.adjuster_name,
            "supervisor_id": self.supervisor_id,
            "external_adjuster": self.external_adjuster,
            "coverage_type": self.coverage_type,
            "policy_limit": float(self.policy_limit) if self.policy_limit else None,
            "deductible": float(self.deductible) if self.deductible else None,
            "fault_percentage": float(self.fault_percentage) if self.fault_percentage else None,
            "liable_party": self.liable_party,
            "comparative_fault": self.comparative_fault,
            "claimant_name": self.claimant_name,
            "claimant_contact": self.claimant_contact,
            "has_claim_level_policy_data": self.has_claim_level_policy_data,
            "subrogation_potential": self.subrogation_potential,
            "subrogation_amount": float(self.subrogation_amount) if self.subrogation_amount else None,
            "litigation_status": self.litigation_status,
            "total_loss": self.total_loss,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Include claim-level policy data if requested and available
        if include_policy_data and self.claim_policy_data:
            data["claim_policy_data"] = self.claim_policy_data

        return data

    def validate_data(self):
        """Validate claim data"""
        # Validate claim number
        if self.claim_number:
            validate_claim_number(self.claim_number)

        # Validate dates
        if self.date_of_loss and self.date_reported:
            if self.date_of_loss > self.date_reported:
                raise ValueError("Date of loss cannot be after date reported")

        # Validate amounts
        if self.fault_percentage is not None:
            if self.fault_percentage < 0 or self.fault_percentage > 100:
                raise ValueError("Fault percentage must be between 0 and 100")

    def is_open(self) -> bool:
        """Check if claim is currently open"""
        return self.status in [ClaimStatus.OPEN.value, ClaimStatus.PENDING.value, ClaimStatus.INVESTIGATION.value]

    def is_closed(self) -> bool:
        """Check if claim is closed"""
        return self.status in [ClaimStatus.CLOSED.value, ClaimStatus.PAID.value, ClaimStatus.DENIED.value]

    def calculate_outstanding_amount(self):
        """Calculate outstanding amount from reserve and paid amounts"""
        reserve = self.reserve_amount or Decimal('0')
        paid = self.paid_amount or Decimal('0')
        recovery = self.recovery_amount or Decimal('0')

        self.outstanding_amount = max(Decimal('0'), reserve - paid + recovery)

    def days_open(self) -> int:
        """Calculate number of days claim has been open"""
        end_date = self.date_closed or date.today()
        return (end_date - self.date_reported).days if self.date_reported else 0

    def add_reserve_line(self, line_type: str, amount: Decimal, description: str = None):
        """Add a reserve line to the claim"""
        if not self.reserve_lines:
            self.reserve_lines = []

        reserve_line = {
            "type": line_type,
            "amount": float(amount),
            "description": description,
            "created_date": datetime.utcnow().isoformat(),
            "status": "active"
        }

        self.reserve_lines.append(reserve_line)
        self._recalculate_reserve_amount()

    def update_reserve_line(self, line_type: str, new_amount: Decimal):
        """Update existing reserve line amount"""
        if not self.reserve_lines:
            return

        for line in self.reserve_lines:
            if line.get("type") == line_type and line.get("status") == "active":
                line["amount"] = float(new_amount)
                line["updated_date"] = datetime.utcnow().isoformat()
                break

        self._recalculate_reserve_amount()

    def _recalculate_reserve_amount(self):
        """Recalculate total reserve amount from reserve lines"""
        if not self.reserve_lines:
            self.reserve_amount = Decimal('0')
            return

        total = Decimal('0')
        for line in self.reserve_lines:
            if line.get("status") == "active":
                total += Decimal(str(line.get("amount", 0)))

        self.reserve_amount = total

    def set_claim_level_policy_data(self, policy_data: dict):
        """Set claim-level policy override data"""
        self.claim_policy_data = policy_data
        self.has_claim_level_policy_data = True

    def clear_claim_level_policy_data(self):
        """Clear claim-level policy override data"""
        self.claim_policy_data = None
        self.has_claim_level_policy_data = False

    def get_effective_policy_data(self, field: str):
        """Get effective policy data (claim-level override or original policy)"""
        # First check claim-level override
        if self.has_claim_level_policy_data and self.claim_policy_data:
            if field in self.claim_policy_data:
                return self.claim_policy_data[field]

        # Fall back to original policy data
        if self.policy:
            return getattr(self.policy, field, None)

        return None

    def requires_approval(self) -> bool:
        """Check if claim requires supervisor approval"""
        approval_thresholds = {
            "reserve_amount": Decimal('50000'),  # $50,000
            "settlement_amount": Decimal('25000'),  # $25,000
        }

        if self.reserve_amount and self.reserve_amount > approval_thresholds["reserve_amount"]:
            return True

        if self.settlement_amount and self.settlement_amount > approval_thresholds["settlement_amount"]:
            return True

        return False

    def update_search_vector(self):
        """Update search vector for full-text search"""
        search_parts = []

        # Add searchable fields
        if self.claim_number:
            search_parts.append(self.claim_number)
        if self.loss_description:
            search_parts.append(self.loss_description)
        if self.claimant_name:
            search_parts.append(self.claimant_name)
        if self.adjuster_name:
            search_parts.append(self.adjuster_name)
        if self.loss_location:
            search_parts.append(self.loss_location)

        self.search_vector = " ".join(search_parts).lower()

    def close_claim(self, close_reason: str = None):
        """Close the claim"""
        self.status = ClaimStatus.CLOSED.value
        self.date_closed = date.today()
        if close_reason:
            if not self.investigation_notes:
                self.investigation_notes = ""
            self.investigation_notes += f"\n\nClaim closed: {close_reason}"

    def reopen_claim(self, reopen_reason: str):
        """Reopen a closed claim"""
        self.status = ClaimStatus.OPEN.value
        self.date_closed = None
        if not self.investigation_notes:
            self.investigation_notes = ""
        self.investigation_notes += f"\n\nClaim reopened: {reopen_reason}"