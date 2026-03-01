from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, JSON, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(100), unique=True, nullable=False, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False, index=True)

    payment_method = Column(String(50), nullable=False)  # ach, wire, card, stripe, global_payout
    payment_type = Column(String(100), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, issued, void, reversed

    # Reserve and tax info
    is_eroding = Column(Boolean, default=True)  # Whether payment erodes reserve
    reserve_lines = Column(JSON, nullable=True)  # Allocation across multiple reserve lines
    is_tax_reportable = Column(Boolean, default=False)
    tax_id_number = Column(String(500), nullable=True)  # Encrypted

    # Payment dates
    payment_date = Column(Date, nullable=True)

    # Void info
    void_date = Column(Date, nullable=True)
    void_reason = Column(String(500), nullable=True)

    # Reversal info
    reversal_date = Column(Date, nullable=True)
    reversal_reason = Column(String(500), nullable=True)

    # Reissue info
    reissue_date = Column(Date, nullable=True)
    original_payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)

    # Audit fields
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PaymentDetail(Base):
    __tablename__ = "payment_details"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False, index=True)

    payee_type = Column(String(50), nullable=False)  # vendor, claimant, provider
    payee_id = Column(Integer, nullable=True)  # FK to Vendor or User
    payee_name = Column(String(255), nullable=False)

    payment_portion = Column(Numeric(15, 2), nullable=False)
    deduction_amount = Column(Numeric(15, 2), nullable=True)
    deduction_reason = Column(String(500), nullable=True)

    banking_info = Column(JSON, nullable=True)  # Encrypted banking details for EFT/wire

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
