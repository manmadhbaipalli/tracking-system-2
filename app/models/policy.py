"""
Policy entities with vehicle details, location info, coverage data, and search indexes.

Supports:
- Advanced policy search with 9+ criteria
- Vehicle information storage
- Location details with address normalization
- Coverage information with limits and deductibles
- Performance-optimized database indexes
"""

import uuid
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Date, Numeric, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Policy(Base):
    """Policy model for insurance policy management."""

    __tablename__ = "policies"

    # Core policy information
    policy_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    policy_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    policy_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE"
    )
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    expiration_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # Insured information
    insured_first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    insured_last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    organizational_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        index=True
    )
    ssn_tin_encrypted: Mapped[Optional[str]] = mapped_column(
        String(255),  # Encrypted value
        nullable=True
    )
    ssn_tin_hash: Mapped[Optional[str]] = mapped_column(
        String(64),  # Hash for searching
        nullable=True,
        index=True
    )

    # Location information
    policy_address: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    policy_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    policy_state: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        index=True
    )
    policy_zip: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True
    )

    # Vehicle information (stored as JSON)
    vehicle_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    # Example structure:
    # {
    #   "year": 2023,
    #   "make": "Toyota",
    #   "model": "Camry",
    #   "vin": "1HGBH41JXMN109186",
    #   "color": "Blue",
    #   "license_plate": "ABC123"
    # }

    # Coverage information (stored as JSON)
    coverage_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    # Example structure:
    # {
    #   "liability": {
    #     "limit": 100000,
    #     "deductible": 500
    #   },
    #   "comprehensive": {
    #     "limit": 50000,
    #     "deductible": 250
    #   }
    # }

    # Premium and financial information
    premium_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    deductible_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    # Additional metadata
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    underwriter: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Loss date for search (can be different from effective date)
    loss_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True
    )

    # Relationships
    claims: Mapped[list["Claim"]] = relationship(
        "Claim",
        back_populates="policy",
        lazy="select"
    )

    # Composite indexes for search performance
    __table_args__ = (
        Index("idx_policy_number_type", "policy_number", "policy_type"),
        Index("idx_insured_name", "insured_last_name", "insured_first_name"),
        Index("idx_policy_location", "policy_state", "policy_city", "policy_zip"),
        Index("idx_policy_dates", "effective_date", "expiration_date"),
        Index("idx_policy_status_type", "policy_status", "policy_type"),
        Index("idx_policy_search_combo", "policy_state", "policy_type", "policy_status"),
    )

    def __repr__(self) -> str:
        return (f"<Policy(id={self.id}, policy_number={self.policy_number}, "
                f"insured={self.insured_last_name}, {self.insured_first_name})>")

    @property
    def insured_name(self) -> str:
        """Get formatted insured name."""
        if self.organizational_name:
            return self.organizational_name
        return f"{self.insured_first_name} {self.insured_last_name}"

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        address_parts = []
        if self.policy_address:
            address_parts.append(self.policy_address)
        address_parts.extend([self.policy_city, self.policy_state, self.policy_zip])
        return ", ".join(filter(None, address_parts))

    @property
    def is_active(self) -> bool:
        """Check if policy is currently active."""
        today = date.today()
        return (
            self.policy_status == "ACTIVE" and
            self.effective_date <= today <= self.expiration_date
        )

    @property
    def is_expired(self) -> bool:
        """Check if policy is expired."""
        return date.today() > self.expiration_date

    def get_vehicle_info(self) -> Dict[str, Any]:
        """Get vehicle information safely."""
        return self.vehicle_details or {}

    def get_coverage_info(self) -> Dict[str, Any]:
        """Get coverage information safely."""
        return self.coverage_details or {}

    def get_coverage_limit(self, coverage_type: str) -> Optional[Decimal]:
        """Get coverage limit for a specific coverage type."""
        coverage = self.get_coverage_info().get(coverage_type, {})
        limit = coverage.get("limit")
        return Decimal(str(limit)) if limit is not None else None

    def get_coverage_deductible(self, coverage_type: str) -> Optional[Decimal]:
        """Get deductible for a specific coverage type."""
        coverage = self.get_coverage_info().get(coverage_type, {})
        deductible = coverage.get("deductible")
        return Decimal(str(deductible)) if deductible is not None else None

    def days_until_expiration(self) -> int:
        """Get number of days until policy expires."""
        return (self.expiration_date - date.today()).days