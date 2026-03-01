from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(255), nullable=False, index=True)
    vendor_type = Column(String(100), nullable=False)  # contractor, medical_provider, attorney

    payment_method_verified = Column(Boolean, default=False)
    kyc_status = Column(String(50), default="pending")  # pending, verified, failed

    tax_id = Column(String(500), nullable=True)  # Encrypted
    banking_info = Column(JSON, nullable=True)  # Encrypted banking details
    stripe_account_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
