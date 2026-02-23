"""
Payment transactions with multiple payees, reserve allocation, and complex payment lifecycle management.

Supports:
- Payment transactions with complex state machines
- Multiple payee support via many-to-many relationships
- Reserve line allocation with erosion tracking
- Multiple payment methods (ACH, wire, cards, Stripe)
- Void/reversal chain tracking for audit compliance
- Tax reporting fields with encrypted TIN storage
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, Date, Numeric, JSON, Text, ForeignKey, Boolean, Enum as SQLEnum, Index, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, GUID


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    VOIDED = "VOIDED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""

    ACH = "ACH"
    WIRE = "WIRE"
    CHECK = "CHECK"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    STRIPE_CONNECT = "STRIPE_CONNECT"
    GLOBAL_PAYOUT = "GLOBAL_PAYOUT"


class PaymentType(str, Enum):
    """Payment type enumeration."""

    CLAIM_PAYMENT = "CLAIM_PAYMENT"
    SETTLEMENT = "SETTLEMENT"
    MEDICAL = "MEDICAL"
    VENDOR = "VENDOR"
    REFUND = "REFUND"
    EXPENSE = "EXPENSE"
    RESERVE_TRANSFER = "RESERVE_TRANSFER"


# Association table for payment-payee many-to-many relationship
payment_payee_table = Table(
    "payment_payees",
    Base.metadata,
    Column("payment_id", GUID, ForeignKey("payments.id"), primary_key=True),
    Column("payee_id", GUID, ForeignKey("payees.id"), primary_key=True),
)


class Payee(Base):
    """Payee model for payment recipients."""

    __tablename__ = "payees"

    # Basic information
    payee_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )  # INDIVIDUAL, BUSINESS, VENDOR, MEDICAL_PROVIDER
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    business_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )

    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True
    )
    zip_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )
    country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="US"
    )

    # Tax information (encrypted)
    tin_encrypted: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    tin_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True
    )
    tax_reportable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Banking information (encrypted)
    banking_details_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    # When decrypted, contains:
    # {
    #   "account_number": "****1234",
    #   "routing_number": "021000021",
    #   "bank_name": "Chase Bank",
    #   "account_type": "CHECKING"
    # }

    # KYC/Identity verification
    identity_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    verification_documents: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Relationships
    payment_allocations: Mapped[List["PaymentPayee"]] = relationship(
        "PaymentPayee",
        back_populates="payee",
        lazy="select"
    )

    def __repr__(self) -> str:
        name = self.business_name or f"{self.first_name} {self.last_name}"
        return f"<Payee(id={self.id}, name={name}, type={self.payee_type})>"

    @property
    def display_name(self) -> str:
        """Get display name for the payee."""
        if self.business_name:
            return self.business_name
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address, self.city, self.state, self.zip_code, self.country]
        return ", ".join(filter(None, parts))


class Payment(Base):
    """Payment model for transaction management."""

    __tablename__ = "payments"

    # Core payment information
    payment_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("claims.id"),
        nullable=True,
        index=True
    )
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("policies.id"),
        nullable=True,
        index=True
    )

    # Payment details
    payment_type: Mapped[PaymentType] = mapped_column(
        SQLEnum(PaymentType),
        nullable=False
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod),
        nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True
    )

    # Financial information
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD"
    )

    # Reserve allocation
    reserve_lines: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    # Example structure:
    # {
    #   "allocations": [
    #     {
    #       "reserve_line": "BODILY_INJURY",
    #       "amount": 2500.00,
    #       "eroding": true
    #     },
    #     {
    #       "reserve_line": "PROPERTY_DAMAGE",
    #       "amount": 1500.00,
    #       "eroding": false
    #     }
    #   ]
    # }

    # Tax withholding
    tax_withheld: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )
    withholding_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Payment dates
    payment_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    processed_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )

    # External system references
    external_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    external_system: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    # Void/Reversal tracking
    original_payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("payments.id"),
        nullable=True
    )
    voided_payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("payments.id"),
        nullable=True
    )
    reversal_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Document attachments
    attached_documents: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Payment routing and processing
    routing_rules_applied: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    processing_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Compliance and audit
    compliance_checks: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    audit_trail: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Notes
    payment_memo: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    claim: Mapped[Optional["Claim"]] = relationship(
        "Claim",
        back_populates="payments",
        lazy="select"
    )
    policy: Mapped[Optional["Policy"]] = relationship(
        "Policy",
        lazy="select"
    )
    payee_allocations: Mapped[List["PaymentPayee"]] = relationship(
        "PaymentPayee",
        back_populates="payment",
        lazy="select",
        cascade="all, delete-orphan"
    )
    original_payment: Mapped[Optional["Payment"]] = relationship(
        "Payment",
        foreign_keys=[original_payment_id],
        remote_side=[id],
        lazy="select"
    )
    voided_payment: Mapped[Optional["Payment"]] = relationship(
        "Payment",
        foreign_keys=[voided_payment_id],
        remote_side=[id],
        lazy="select"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_payment_claim_status", "claim_id", "payment_status"),
        Index("idx_payment_type_method", "payment_type", "payment_method"),
        Index("idx_payment_dates", "payment_date", "due_date"),
        Index("idx_payment_external", "external_payment_id", "external_system"),
        Index("idx_payment_processing", "payment_status", "processed_date"),
    )

    def __repr__(self) -> str:
        return (f"<Payment(id={self.id}, payment_number={self.payment_number}, "
                f"amount={self.total_amount}, status={self.payment_status})>")

    @property
    def net_amount(self) -> Decimal:
        """Get net payment amount after tax withholding."""
        return self.total_amount - self.tax_withheld

    @property
    def is_processed(self) -> bool:
        """Check if payment has been processed."""
        return self.payment_status in [PaymentStatus.COMPLETED, PaymentStatus.VOIDED, PaymentStatus.REVERSED]

    @property
    def can_be_voided(self) -> bool:
        """Check if payment can be voided."""
        return self.payment_status == PaymentStatus.COMPLETED and not self.voided_payment_id

    @property
    def is_positive_amount(self) -> bool:
        """Check if payment amount is positive."""
        return self.total_amount > 0

    def get_total_allocated(self) -> Decimal:
        """Get total amount allocated to payees."""
        return sum(allocation.amount for allocation in self.payee_allocations)

    def get_reserve_allocation(self, reserve_line: str) -> Optional[Decimal]:
        """Get allocation amount for a specific reserve line."""
        if not self.reserve_lines or "allocations" not in self.reserve_lines:
            return None

        for allocation in self.reserve_lines["allocations"]:
            if allocation.get("reserve_line") == reserve_line:
                return Decimal(str(allocation.get("amount", 0)))

        return None

    def add_payee_allocation(self, payee_id: uuid.UUID, amount: Decimal,
                           allocation_type: str = "PAYMENT") -> "PaymentPayee":
        """Add a payee allocation to this payment."""
        allocation = PaymentPayee(
            payment_id=self.id,
            payee_id=payee_id,
            amount=amount,
            allocation_type=allocation_type
        )
        self.payee_allocations.append(allocation)
        return allocation

    def void_payment(self, reason: str) -> None:
        """Void the payment."""
        if not self.can_be_voided:
            raise ValueError("Payment cannot be voided")

        self.payment_status = PaymentStatus.VOIDED
        self.reversal_reason = reason
        self.processed_date = datetime.utcnow()


class PaymentPayee(Base):
    """Association model for payment-payee relationships with allocation details."""

    __tablename__ = "payment_payee_allocations"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("payments.id"),
        primary_key=True
    )
    payee_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("payees.id"),
        primary_key=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    allocation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PAYMENT"
    )
    deduction_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    payment: Mapped["Payment"] = relationship(
        "Payment",
        back_populates="payee_allocations",
        lazy="select"
    )
    payee: Mapped["Payee"] = relationship(
        "Payee",
        back_populates="payment_allocations",
        lazy="select"
    )

    def __repr__(self) -> str:
        return (f"<PaymentPayee(payment_id={self.payment_id}, "
                f"payee_id={self.payee_id}, amount={self.amount})>")

    @property
    def effective_amount(self) -> Decimal:
        """Get effective payment amount after deductions."""
        return self.amount - self.deduction_amount