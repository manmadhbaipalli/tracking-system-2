import enum
from decimal import Decimal
from sqlalchemy import (
    String, Boolean, Enum as SAEnum, Numeric, Date, Index, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, AuditMixin


class PolicyStatus(str, enum.Enum):
    """Policy lifecycle statuses."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PolicyType(str, enum.Enum):
    """Types of insurance policies."""
    AUTO = "AUTO"
    PROPERTY = "PROPERTY"
    LIABILITY = "LIABILITY"
    WORKERS_COMP = "WORKERS_COMP"
    HEALTH = "HEALTH"
    OTHER = "OTHER"


class CoverageType(str, enum.Enum):
    """Coverage types."""
    LIABILITY = "LIABILITY"
    COLLISION = "COLLISION"
    COMPREHENSIVE = "COMPREHENSIVE"
    UNINSURED_MOTORIST = "UNINSURED_MOTORIST"
    MEDICAL_PAYMENTS = "MEDICAL_PAYMENTS"
    OTHER = "OTHER"


class Policy(AuditMixin, Base):
    """Insurance policies with complete lifecycle management."""
    __tablename__ = "policies"
    __table_args__ = (
        Index("idx_policies_policy_number", "policy_number"),
        Index("idx_policies_status", "status"),
        Index("idx_policies_insured_id", "insured_id"),
        Index("idx_policies_effective_date", "effective_date"),
    )

    policy_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    insured_id: Mapped[int] = mapped_column(nullable=False)
    policy_type: Mapped[PolicyType] = mapped_column(
        SAEnum(PolicyType), nullable=False
    )
    status: Mapped[PolicyStatus] = mapped_column(
        SAEnum(PolicyStatus), default=PolicyStatus.ACTIVE, nullable=False
    )
    effective_date: Mapped[str] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[str] = mapped_column(Date, nullable=False)
    premium_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    deductible_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )

    # Relationships
    insured: Mapped["Insured"] = relationship(back_populates="policies")
    coverages: Mapped[list["Coverage"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )
    claims: Mapped[list["Claim"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )
    endorsements: Mapped[list["Endorsement"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )


class Insured(AuditMixin, Base):
    """Party information (insured, claimant, payee)."""
    __tablename__ = "insureds"
    __table_args__ = (
        Index("idx_insureds_email", "email"),
        Index("idx_insureds_tax_id", "tax_id"),
        Index("idx_insureds_name", "first_name", "last_name"),
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    tax_id: Mapped[str] = mapped_column(String(50), nullable=True)  # SSN/TIN (encrypted)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(2), nullable=True)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=True)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    policies: Mapped[list[Policy]] = relationship(
        back_populates="insured", cascade="all, delete-orphan"
    )


class Coverage(AuditMixin, Base):
    """Coverage types, limits, and deductibles."""
    __tablename__ = "coverages"
    __table_args__ = (
        Index("idx_coverages_policy_id", "policy_id"),
    )

    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    coverage_type: Mapped[CoverageType] = mapped_column(
        SAEnum(CoverageType), nullable=False
    )
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    deductible_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationships
    policy: Mapped[Policy] = relationship(back_populates="coverages")


class Vehicle(AuditMixin, Base):
    """Vehicle details for auto policies."""
    __tablename__ = "vehicles"
    __table_args__ = (
        Index("idx_vehicles_policy_id", "policy_id"),
        Index("idx_vehicles_vin", "vin"),
    )

    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    vin: Mapped[str] = mapped_column(String(17), unique=True, nullable=False)
    license_plate: Mapped[str] = mapped_column(String(20), nullable=True)


class Location(AuditMixin, Base):
    """Location/address details for policies."""
    __tablename__ = "locations"
    __table_args__ = (
        Index("idx_locations_policy_id", "policy_id"),
    )

    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)


class Endorsement(AuditMixin, Base):
    """Policy modifications and endorsements."""
    __tablename__ = "endorsements"
    __table_args__ = (
        Index("idx_endorsements_policy_id", "policy_id"),
    )

    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    endorsement_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    effective_date: Mapped[str] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[str] = mapped_column(Date, nullable=True)

    # Relationships
    policy: Mapped[Policy] = relationship(back_populates="endorsements")
