from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, JSON, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.models.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(100), unique=True, nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False, index=True)
    loss_date = Column(Date, nullable=False, index=True)
    claim_status = Column(String(50), nullable=False, default="open", index=True)  # open, closed, paid, denied
    description = Column(String(2000), nullable=True)

    # Claim-level policy data (for unverified policies)
    claim_level_policy_data = Column(JSON, nullable=True)

    # Injury and incident details
    injury_incident_details = Column(JSON, nullable=True)
    coding_information = Column(JSON, nullable=True)
    carrier_involvement = Column(JSON, nullable=True)

    # Subrogation
    referred_to_subrogation = Column(Boolean, default=False)
    subrogation_date = Column(Date, nullable=True)

    # Scheduled payments
    scheduled_payment_applicable = Column(Boolean, default=False)
    scheduled_payment_type = Column(String(100), nullable=True)
    scheduled_payment_total = Column(Numeric(15, 2), nullable=True)
    scheduled_payment_balance = Column(Numeric(15, 2), nullable=True)
    scheduled_payment_current_due = Column(Numeric(15, 2), nullable=True)
    scheduled_payment_recipient = Column(String(255), nullable=True)

    # Audit fields
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
