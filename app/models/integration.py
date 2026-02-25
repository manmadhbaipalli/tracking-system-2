import enum
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Index, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, AuditMixin


class ScheduledPaymentStatus(str, enum.Enum):
    """Scheduled payment statuses."""
    PENDING = "PENDING"
    DUE = "DUE"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class ScheduledPayment(AuditMixin, Base):
    """Subrogation scheduled payment tracking."""
    __tablename__ = "scheduled_payments"
    __table_args__ = (
        Index("idx_scheduled_payments_claim_id", "claim_id"),
        Index("idx_scheduled_payments_status", "status"),
    )

    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    payee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scheduled_date: Mapped[str] = mapped_column(nullable=False)
    payment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    remaining_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[ScheduledPaymentStatus] = mapped_column(
        SAEnum(ScheduledPaymentStatus), default=ScheduledPaymentStatus.PENDING, nullable=False
    )

    # Relationships
    claim: Mapped["Claim"] = relationship(back_populates="scheduled_payments")


class ExternalEstimate(AuditMixin, Base):
    """Payable line items from external estimates (Xactimate/XactAnalysis)."""
    __tablename__ = "external_estimates"
    __table_args__ = (
        Index("idx_external_estimates_claim_id", "claim_id"),
    )

    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    estimate_number: Mapped[str] = mapped_column(String(100), nullable=False)
    source_system: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "XACTIMATE"
    line_item_description: Mapped[str] = mapped_column(Text, nullable=True)
    item_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    is_payable: Mapped[bool] = mapped_column(default=False, nullable=False)
    additional_metadata: Mapped[str] = mapped_column(Text, nullable=True)


class PaymentRoutingRule(AuditMixin, Base):
    """Business rules for payment routing based on payee, type, and conditions."""
    __tablename__ = "payment_routing_rules"

    rule_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payee_filter: Mapped[str] = mapped_column(Text, nullable=True)  # JSON filter
    payment_type_filter: Mapped[str] = mapped_column(String(100), nullable=True)
    routing_target: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class TaxReportablePayment(AuditMixin, Base):
    """Tax reporting details for payments."""
    __tablename__ = "tax_reportable_payments"
    __table_args__ = (
        Index("idx_tax_reportable_payments_payee_id", "payee_id"),
    )

    payee_id: Mapped[int] = mapped_column(ForeignKey("payees.id"), nullable=False)
    tax_year: Mapped[int] = mapped_column(nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_form_type: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g., "1099", "W2"
    tax_id: Mapped[str] = mapped_column(String(50), nullable=True)  # Encrypted
    tax_id_type: Mapped[str] = mapped_column(String(20), nullable=True)  # SSN, EIN, ITIN
    additional_info: Mapped[str] = mapped_column(Text, nullable=True)
