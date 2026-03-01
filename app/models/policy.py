from sqlalchemy import Column, Integer, String, DateTime, Date, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String(100), unique=True, nullable=False, index=True)
    insured_first_name = Column(String(255), nullable=False, index=True)
    insured_last_name = Column(String(255), nullable=False, index=True)
    organization_name = Column(String(255), nullable=True, index=True)
    ssn_tin = Column(String(500), nullable=True)  # Encrypted
    policy_type = Column(String(100), nullable=False, index=True)
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="active")  # active, expired, cancelled

    # Vehicle details
    vehicle_year = Column(Integer, nullable=True)
    vehicle_make = Column(String(100), nullable=True)
    vehicle_model = Column(String(100), nullable=True)
    vehicle_vin = Column(String(100), nullable=True)

    # Location details
    address = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True, index=True)
    state = Column(String(50), nullable=True, index=True)
    zip = Column(String(20), nullable=True, index=True)

    # Coverage details (stored as JSON)
    coverage_types = Column(JSON, nullable=True)  # List of coverage types
    coverage_limits = Column(JSON, nullable=True)  # Dict of coverage limits
    coverage_deductibles = Column(JSON, nullable=True)  # Dict of deductibles

    # Audit fields
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
