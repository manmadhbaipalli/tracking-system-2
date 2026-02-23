"""
Claims linked to policies with claim-level policy overrides, subrogation support, and audit tracking.

Supports:
- Claims linked to policies with foreign key relationships
- Claim-level policy data overrides with separate tracking
- Comprehensive claim status workflow
- Subrogation support and carrier involvement
- Injury incident details and coding information
"""

import uuid
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, Date, Numeric, JSON, Text, ForeignKey, Boolean, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, GUID


class ClaimStatus(str, Enum):
    """Claim status enumeration."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PAID = "PAID"
    DENIED = "DENIED"
    PENDING = "PENDING"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"


class ClaimType(str, Enum):
    """Claim type enumeration."""

    AUTO = "AUTO"
    PROPERTY = "PROPERTY"
    LIABILITY = "LIABILITY"
    WORKERS_COMP = "WORKERS_COMP"
    GENERAL = "GENERAL"


class Claim(Base):
    """Claim model for insurance claims management."""

    __tablename__ = "claims"

    # Core claim information
    claim_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("policies.id"),
        nullable=False,
        index=True
    )
    claim_type: Mapped[ClaimType] = mapped_column(
        SQLEnum(ClaimType),
        nullable=False
    )
    claim_status: Mapped[ClaimStatus] = mapped_column(
        SQLEnum(ClaimStatus),
        nullable=False,
        default=ClaimStatus.OPEN,
        index=True
    )

    # Claim dates
    date_of_loss: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    date_reported: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow
    )
    date_closed: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )

    # Financial information
    claim_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    reserve_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )
    deductible_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    # Claim details
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    location_of_loss: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    # Claim-level policy overrides (separate from main policy)
    has_policy_overrides: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    policy_override_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    # Example structure:
    # {
    #   "insured_first_name": "John",
    #   "insured_last_name": "Doe",
    #   "policy_address": "123 Override St",
    #   "vehicle_details": {...},
    #   "coverage_details": {...},
    #   "override_reason": "Unverified policy data",
    #   "override_date": "2024-01-01T00:00:00"
    # }

    # Subrogation support
    subrogation_potential: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    subrogation_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    related_claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("claims.id"),
        nullable=True
    )

    # Injury and incident details
    injury_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    # Example structure:
    # {
    #   "injury_type": "Bodily Injury",
    #   "body_parts": ["Back", "Neck"],
    #   "severity": "Minor",
    #   "medical_treatment": true,
    #   "hospitalization": false,
    #   "icd_codes": ["S13.4XXA", "M54.2"]
    # }

    # Coding information
    coding_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    # Example structure:
    # {
    #   "coverage_codes": ["BI", "PD", "COMP"],
    #   "cause_of_loss": "COL001",
    #   "peril_code": "PERIL_COLLISION",
    #   "icd_codes": ["S13.4XXA"],
    #   "cpt_codes": ["99213", "73030"]
    # }

    # Carrier involvement
    carrier_involvement: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    # Example structure:
    # {
    #   "other_carriers": [
    #     {
    #       "carrier_name": "State Farm",
    #       "policy_number": "SF123456",
    #       "involvement_type": "At-Fault Party",
    #       "contact_info": {...}
    #     }
    #   ],
    #   "primary_carrier": true,
    #   "coverage_position": "Primary"
    # }

    # Scheduled payments
    scheduled_payments: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    # Example structure:
    # {
    #   "applicable": true,
    #   "payment_type": "Medical",
    #   "total_amount": 5000.00,
    #   "balance": 3000.00,
    #   "current_due": 1000.00,
    #   "recipient_id": "uuid",
    #   "schedule": [...]
    # }

    # Assignment and handling
    adjuster_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    examiner_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    attorney_involved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Additional notes and metadata
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    external_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    policy: Mapped["Policy"] = relationship(
        "Policy",
        back_populates="claims",
        lazy="select"
    )
    related_claim: Mapped[Optional["Claim"]] = relationship(
        "Claim",
        remote_side=[id],
        lazy="select"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="claim",
        lazy="select"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_claim_policy_status", "policy_id", "claim_status"),
        Index("idx_claim_dates", "date_of_loss", "date_reported"),
        Index("idx_claim_type_status", "claim_type", "claim_status"),
        Index("idx_claim_adjuster", "adjuster_id"),
        Index("idx_claim_subrogation", "subrogation_potential"),
    )

    def __repr__(self) -> str:
        return (f"<Claim(id={self.id}, claim_number={self.claim_number}, "
                f"status={self.claim_status}, policy_id={self.policy_id})>")

    @property
    def is_open(self) -> bool:
        """Check if claim is open."""
        return self.claim_status in [ClaimStatus.OPEN, ClaimStatus.PENDING, ClaimStatus.UNDER_INVESTIGATION]

    @property
    def is_closed(self) -> bool:
        """Check if claim is closed."""
        return self.claim_status in [ClaimStatus.CLOSED, ClaimStatus.PAID, ClaimStatus.DENIED]

    @property
    def outstanding_reserve(self) -> Decimal:
        """Calculate outstanding reserve amount."""
        if not self.reserve_amount:
            return Decimal('0')
        return self.reserve_amount - self.paid_amount

    @property
    def days_since_loss(self) -> int:
        """Get number of days since date of loss."""
        return (date.today() - self.date_of_loss).days

    def get_effective_policy_data(self) -> Dict[str, Any]:
        """Get effective policy data (overrides if available, otherwise original policy)."""
        if self.has_policy_overrides and self.policy_override_data:
            return self.policy_override_data

        # Fallback to policy data
        return {
            "insured_first_name": self.policy.insured_first_name,
            "insured_last_name": self.policy.insured_last_name,
            "policy_address": self.policy.policy_address,
            "policy_city": self.policy.policy_city,
            "policy_state": self.policy.policy_state,
            "policy_zip": self.policy.policy_zip,
            "vehicle_details": self.policy.vehicle_details,
            "coverage_details": self.policy.coverage_details
        }

    def set_policy_override(self, override_data: Dict[str, Any], reason: str) -> None:
        """Set claim-level policy data override."""
        self.has_policy_overrides = True
        self.policy_override_data = {
            **override_data,
            "override_reason": reason,
            "override_date": datetime.utcnow().isoformat()
        }

    def clear_policy_override(self) -> None:
        """Clear claim-level policy data override."""
        self.has_policy_overrides = False
        self.policy_override_data = None

    def can_be_closed(self) -> bool:
        """Check if claim can be closed based on business rules."""
        # Add business logic here
        return self.claim_status == ClaimStatus.OPEN and self.outstanding_reserve <= 0

    def close_claim(self, reason: Optional[str] = None) -> None:
        """Close the claim."""
        if self.can_be_closed():
            self.claim_status = ClaimStatus.CLOSED
            self.date_closed = datetime.utcnow()
            if reason:
                self.internal_notes = f"{self.internal_notes or ''}\nClosed: {reason}".strip()