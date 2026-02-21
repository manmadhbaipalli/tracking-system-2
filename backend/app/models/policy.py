"""
Claims Service Platform - Policy Model

Policy entity with encrypted SSN/TIN fields, vehicle/location/coverage details, and search indexes.
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Decimal, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

from app.core.database import Base, EncryptedString
from app.utils.validators import validate_policy_number, validate_ssn, validate_tin, validate_zip_code, validate_state_code


class PolicyType(enum.Enum):
    """Policy type enumeration"""
    AUTO = "auto"
    HOME = "home"
    LIFE = "life"
    HEALTH = "health"
    COMMERCIAL = "commercial"
    UMBRELLA = "umbrella"
    WORKERS_COMP = "workers_comp"
    LIABILITY = "liability"


class PolicyStatus(enum.Enum):
    """Policy status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"
    SUSPENDED = "suspended"


class CoverageType(enum.Enum):
    """Coverage type enumeration"""
    LIABILITY = "liability"
    COLLISION = "collision"
    COMPREHENSIVE = "comprehensive"
    UNINSURED_MOTORIST = "uninsured_motorist"
    PERSONAL_INJURY = "personal_injury"
    PROPERTY_DAMAGE = "property_damage"
    MEDICAL_PAYMENTS = "medical_payments"
    RENTAL_REIMBURSEMENT = "rental_reimbursement"


class Policy(Base):
    """Policy model with encrypted PII fields and comprehensive details"""

    __tablename__ = "policies"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Policy identification
    policy_number = Column(String(20), unique=True, nullable=False, index=True)
    policy_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=PolicyStatus.ACTIVE.value, index=True)

    # Policy dates
    effective_date = Column(Date, nullable=False, index=True)
    expiration_date = Column(Date, nullable=False, index=True)
    loss_date = Column(Date, index=True)  # For search purposes

    # Insured information
    insured_first_name = Column(String(100), nullable=False, index=True)
    insured_last_name = Column(String(100), nullable=False, index=True)
    insured_full_name = Column(String(200), nullable=False, index=True)

    # Encrypted PII fields
    ssn = Column(EncryptedString(255), index=False)  # Don't index encrypted fields
    tin = Column(EncryptedString(255), index=False)

    # Organization information (for commercial policies)
    organization_name = Column(String(200), index=True)
    organization_type = Column(String(50))

    # Contact information
    email = Column(String(255))
    phone = Column(String(20))
    mobile_phone = Column(String(20))

    # Location details
    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200))
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(2), nullable=False, index=True)
    zip_code = Column(String(10), nullable=False, index=True)
    country = Column(String(3), default="USA")

    # Premium and financial information
    premium_amount = Column(Decimal(12, 2))
    deductible_amount = Column(Decimal(10, 2))
    policy_limit = Column(Decimal(12, 2))

    # Vehicle details (for auto policies)
    vehicle_year = Column(Integer)
    vehicle_make = Column(String(50))
    vehicle_model = Column(String(50))
    vehicle_vin = Column(String(17))
    vehicle_color = Column(String(30))
    vehicle_license_plate = Column(String(20))

    # Coverage details (JSON field for flexibility)
    coverage_details = Column(JSON)  # Array of coverage objects
    coverage_limits = Column(JSON)   # Coverage limits by type
    deductibles = Column(JSON)       # Deductibles by coverage type

    # Additional policy details
    agent_name = Column(String(100))
    agent_code = Column(String(20))
    branch_code = Column(String(20))
    underwriter = Column(String(100))

    # Policy terms and conditions
    policy_terms = Column(Text)
    special_conditions = Column(Text)
    endorsements = Column(JSON)  # Array of endorsement objects

    # Risk assessment
    risk_score = Column(Integer)
    risk_factors = Column(JSON)

    # Compliance and regulatory
    state_filing = Column(String(100))
    regulatory_code = Column(String(50))

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
    search_vector = Column(Text)  # Full-text search vector

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    claims = relationship("Claim", back_populates="policy")
    payments = relationship("Payment", back_populates="policy")

    def __repr__(self):
        return f"<Policy(id={self.id}, policy_number='{self.policy_number}', insured='{self.insured_full_name}')>"

    def to_dict(self, mask_pii: bool = True):
        """Convert policy to dictionary with optional PII masking"""
        from app.core.security import mask_ssn

        data = {
            "id": self.id,
            "policy_number": self.policy_number,
            "policy_type": self.policy_type,
            "status": self.status,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "loss_date": self.loss_date.isoformat() if self.loss_date else None,
            "insured_first_name": self.insured_first_name,
            "insured_last_name": self.insured_last_name,
            "insured_full_name": self.insured_full_name,
            "organization_name": self.organization_name,
            "organization_type": self.organization_type,
            "email": self.email,
            "phone": self.phone,
            "mobile_phone": self.mobile_phone,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "premium_amount": float(self.premium_amount) if self.premium_amount else None,
            "deductible_amount": float(self.deductible_amount) if self.deductible_amount else None,
            "policy_limit": float(self.policy_limit) if self.policy_limit else None,
            "vehicle_year": self.vehicle_year,
            "vehicle_make": self.vehicle_make,
            "vehicle_model": self.vehicle_model,
            "vehicle_vin": self.vehicle_vin,
            "vehicle_color": self.vehicle_color,
            "vehicle_license_plate": self.vehicle_license_plate,
            "coverage_details": self.coverage_details,
            "coverage_limits": self.coverage_limits,
            "deductibles": self.deductibles,
            "agent_name": self.agent_name,
            "agent_code": self.agent_code,
            "branch_code": self.branch_code,
            "underwriter": self.underwriter,
            "risk_score": self.risk_score,
            "risk_factors": self.risk_factors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Handle PII fields with masking
        if mask_pii:
            data["ssn"] = mask_ssn(self.ssn) if self.ssn else None
            data["tin"] = mask_ssn(self.tin) if self.tin else None
        else:
            data["ssn"] = self.ssn
            data["tin"] = self.tin

        return data

    def validate_data(self):
        """Validate policy data"""
        # Validate policy number
        if self.policy_number:
            validate_policy_number(self.policy_number)

        # Validate SSN if provided
        if self.ssn:
            validate_ssn(self.ssn)

        # Validate TIN if provided
        if self.tin:
            validate_tin(self.tin)

        # Validate state code
        if self.state:
            validate_state_code(self.state)

        # Validate ZIP code
        if self.zip_code:
            validate_zip_code(self.zip_code)

        # Validate policy dates
        if self.effective_date and self.expiration_date:
            if self.effective_date >= self.expiration_date:
                raise ValueError("Effective date must be before expiration date")

    def is_active(self) -> bool:
        """Check if policy is currently active"""
        today = date.today()
        return (
            self.status == PolicyStatus.ACTIVE.value and
            self.effective_date <= today <= self.expiration_date
        )

    def is_expired(self) -> bool:
        """Check if policy is expired"""
        return date.today() > self.expiration_date

    def days_until_expiration(self) -> int:
        """Get number of days until policy expires"""
        if self.expiration_date:
            return (self.expiration_date - date.today()).days
        return 0

    def generate_full_name(self):
        """Generate full name from first and last name"""
        if self.insured_first_name and self.insured_last_name:
            self.insured_full_name = f"{self.insured_first_name} {self.insured_last_name}"
        elif self.organization_name:
            self.insured_full_name = self.organization_name
        elif self.insured_first_name:
            self.insured_full_name = self.insured_first_name
        elif self.insured_last_name:
            self.insured_full_name = self.insured_last_name

    def update_search_vector(self):
        """Update search vector for full-text search"""
        search_parts = []

        # Add all searchable text fields
        if self.policy_number:
            search_parts.append(self.policy_number)
        if self.insured_first_name:
            search_parts.append(self.insured_first_name)
        if self.insured_last_name:
            search_parts.append(self.insured_last_name)
        if self.organization_name:
            search_parts.append(self.organization_name)
        if self.city:
            search_parts.append(self.city)
        if self.state:
            search_parts.append(self.state)
        if self.zip_code:
            search_parts.append(self.zip_code)
        if self.vehicle_make:
            search_parts.append(self.vehicle_make)
        if self.vehicle_model:
            search_parts.append(self.vehicle_model)
        if self.vehicle_vin:
            search_parts.append(self.vehicle_vin)

        self.search_vector = " ".join(search_parts).lower()

    def get_coverage_by_type(self, coverage_type: str) -> dict:
        """Get coverage details for specific coverage type"""
        if not self.coverage_details:
            return {}

        for coverage in self.coverage_details:
            if coverage.get("type") == coverage_type:
                return coverage

        return {}

    def add_coverage(self, coverage_type: str, limit: float, deductible: float = 0):
        """Add coverage to policy"""
        if not self.coverage_details:
            self.coverage_details = []

        coverage = {
            "type": coverage_type,
            "limit": limit,
            "deductible": deductible,
            "premium": 0,  # To be calculated
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
        }

        self.coverage_details.append(coverage)

    def remove_coverage(self, coverage_type: str):
        """Remove coverage from policy"""
        if not self.coverage_details:
            return

        self.coverage_details = [
            c for c in self.coverage_details
            if c.get("type") != coverage_type
        ]

    def calculate_total_premium(self) -> Decimal:
        """Calculate total premium from all coverages"""
        if not self.coverage_details:
            return Decimal('0.00')

        total = Decimal('0.00')
        for coverage in self.coverage_details:
            premium = coverage.get("premium", 0)
            total += Decimal(str(premium))

        return total