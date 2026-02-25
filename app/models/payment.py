import enum
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Index, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, AuditMixin


class PaymentMethodType(str, enum.Enum):
    """Payment method types."""
    ACH = "ACH"
    WIRE = "WIRE"
    CARD = "CARD"
    STRIPE = "STRIPE"
    GLOBAL_PAYOUTS = "GLOBAL_PAYOUTS"


class PaymentStatus(str, enum.Enum):
    """Payment lifecycle statuses."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    VOIDED = "VOIDED"
    REVERSED = "REVERSED"


class Payment(AuditMixin, Base):
    """
    Payment transactions linked to claims/policies.
    Supports multiple payment methods, positive/negative/zero amounts.
    """
    __tablename__ = "payments"
    __table_args__ = (
        Index("idx_payments_payment_number", "payment_number"),
        Index("idx_payments_claim_id", "claim_id"),
        Index("idx_payments_policy_id", "policy_id"),
        Index("idx_payments_payee_id", "payee_id"),
        Index("idx_payments_status", "status"),
    )

    payment_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=True)
    payee_id: Mapped[int] = mapped_column(ForeignKey("payees.id"), nullable=False)
    reserve_line_id: Mapped[int] = mapped_column(ForeignKey("reserve_lines.id"), nullable=True)
    payment_method: Mapped[PaymentMethodType] = mapped_column(
        SAEnum(PaymentMethodType), nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    is_eroding: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_tax_reportable: Mapped[bool] = mapped_column(default=False, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    claim: Mapped["Claim"] = relationship(back_populates="payments")
    policy: Mapped["Policy"] = relationship(back_populates="payments")
    payee: Mapped["Payee"] = relationship(back_populates="payments")
    reserve_line: Mapped["ReserveLine"] = relationship(back_populates="payments")
    payment_details: Mapped[list["PaymentDetail"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )
    deductions: Mapped[list["PaymentDeduction"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )
    documents: Mapped[list["PaymentDocument"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )


class Payee(AuditMixin, Base):
    """
    Vendor/claimant onboarding with KYC/identity verification.
    Secure payment method verification.
    """
    __tablename__ = "payees"
    __table_args__ = (
        Index("idx_payees_tax_id", "tax_id"),
        Index("idx_payees_email", "email"),
        Index("idx_payees_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    tax_id: Mapped[str] = mapped_column(String(50), nullable=True)  # Encrypted
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(2), nullable=True)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=True)
    kyc_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    kyc_document_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    payments: Mapped[list[Payment]] = relationship(
        back_populates="payee", cascade="all, delete-orphan"
    )
    payment_methods: Mapped[list["PaymentMethod"]] = relationship(
        back_populates="payee", cascade="all, delete-orphan"
    )


class PaymentMethod(AuditMixin, Base):
    """Payment method details for payees (ACH, Wire, Card, Stripe, etc.)."""
    __tablename__ = "payment_methods"
    __table_args__ = (
        Index("idx_payment_methods_payee_id", "payee_id"),
    )

    payee_id: Mapped[int] = mapped_column(ForeignKey("payees.id"), nullable=False)
    method_type: Mapped[PaymentMethodType] = mapped_column(
        SAEnum(PaymentMethodType), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    account_number: Mapped[str] = mapped_column(String(255), nullable=True)  # Encrypted
    routing_number: Mapped[str] = mapped_column(String(20), nullable=True)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=True)
    account_holder_name: Mapped[str] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    payee: Mapped[Payee] = relationship(back_populates="payment_methods")


class PaymentDetail(AuditMixin, Base):
    """Line items/details for payment transactions."""
    __tablename__ = "payment_details"
    __table_args__ = (
        Index("idx_payment_details_payment_id", "payment_id"),
    )

    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False)
    detail_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    additional_info: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    payment: Mapped[Payment] = relationship(back_populates="payment_details")


class PaymentDeduction(AuditMixin, Base):
    """Tax withholding and other deductions from payments."""
    __tablename__ = "payment_deductions"
    __table_args__ = (
        Index("idx_payment_deductions_payment_id", "payment_id"),
    )

    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False)
    deduction_type: Mapped[str] = mapped_column(String(100), nullable=False)
    deduction_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    payment: Mapped[Payment] = relationship(back_populates="deductions")


class PaymentDocument(AuditMixin, Base):
    """Document attachments to payment transactions."""
    __tablename__ = "payment_documents"
    __table_args__ = (
        Index("idx_payment_documents_payment_id", "payment_id"),
    )

    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_url: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=True)

    # Relationships
    payment: Mapped[Payment] = relationship(back_populates="documents")
