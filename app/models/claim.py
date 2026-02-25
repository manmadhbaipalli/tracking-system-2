import enum
from datetime import date
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Date, Index, ForeignKey, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, AuditMixin


class ClaimStatus(str, enum.Enum):
    """Claim lifecycle statuses."""
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    CLOSED = "CLOSED"
    PAID = "PAID"
    DENIED = "DENIED"


class Claim(AuditMixin, Base):
    """Claims linked to policies with full lifecycle support."""
    __tablename__ = "claims"
    __table_args__ = (
        Index("idx_claims_claim_number", "claim_number"),
        Index("idx_claims_policy_id", "policy_id"),
        Index("idx_claims_status", "status"),
        Index("idx_claims_date_of_loss", "date_of_loss"),
    )

    claim_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    date_of_loss: Mapped[date] = mapped_column(Date, nullable=False)
    date_reported: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ClaimStatus] = mapped_column(
        SAEnum(ClaimStatus), default=ClaimStatus.OPEN, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    injury_details: Mapped[str] = mapped_column(Text, nullable=True)
    carrier_involvement: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    policy: Mapped["Policy"] = relationship(back_populates="claims")
    adjustments: Mapped[list["ClaimAdjustment"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    reserve_lines: Mapped[list["ReserveLine"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    claim_level_policy: Mapped["ClaimLevelPolicy"] = relationship(
        back_populates="claim", uselist=False, cascade="all, delete-orphan"
    )
    other_carrier_info: Mapped["OtherCarrierInfo"] = relationship(
        back_populates="claim", uselist=False, cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    scheduled_payments: Mapped[list["ScheduledPayment"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimAdjustment(AuditMixin, Base):
    """Adjustments and updates to claim values."""
    __tablename__ = "claim_adjustments"
    __table_args__ = (
        Index("idx_claim_adjustments_claim_id", "claim_id"),
    )

    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    adjustment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    adjustment_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    claim: Mapped[Claim] = relationship(back_populates="adjustments")


class ReserveLine(AuditMixin, Base):
    """Reserve allocations for claims."""
    __tablename__ = "reserve_lines"
    __table_args__ = (
        Index("idx_reserve_lines_claim_id", "claim_id"),
    )

    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    reserve_type: Mapped[str] = mapped_column(String(100), nullable=False)
    total_reserve: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    used_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    remaining_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    is_eroding: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    claim: Mapped[Claim] = relationship(back_populates="reserve_lines")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="reserve_line", cascade="all, delete-orphan"
    )


class ClaimLevelPolicy(AuditMixin, Base):
    """
    Claim-specific policy data (when policy is unverified).
    Visual indicator shows when claim-level data is being used.
    """
    __tablename__ = "claim_level_policies"
    __table_args__ = (
        Index("idx_claim_level_policies_claim_id", "claim_id"),
    )

    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    policy_number: Mapped[str] = mapped_column(String(100), nullable=True)
    insured_name: Mapped[str] = mapped_column(String(200), nullable=True)
    policy_type: Mapped[str] = mapped_column(String(100), nullable=True)
    coverage_details: Mapped[str] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    claim: Mapped[Claim] = relationship(back_populates="claim_level_policy")


class OtherCarrierInfo(AuditMixin, Base):
    """Other carrier party and payment information for claims."""
    __tablename__ = "other_carrier_info"
    __table_args__ = (
        Index("idx_other_carrier_info_claim_id", "claim_id"),
    )

    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    carrier_name: Mapped[str] = mapped_column(String(255), nullable=True)
    claim_number: Mapped[str] = mapped_column(String(100), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    payment_info: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    claim: Mapped[Claim] = relationship(back_populates="other_carrier_info")
