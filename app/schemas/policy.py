"""
Policy request/response schemas with search criteria, masking for sensitive data, and validation rules.

Provides Pydantic models for:
- Advanced policy search with 9+ criteria
- Policy CRUD operations with validation
- Sensitive data masking (SSN/TIN)
- Policy details with vehicle and coverage information
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.utils.security import mask_ssn_tin


class PolicySearchRequest(BaseModel):
    """Policy search request schema with multiple search criteria."""

    policy_number: Optional[str] = Field(None, max_length=50, description="Policy number (exact or partial match)")
    insured_first_name: Optional[str] = Field(None, max_length=100, description="Insured first name (partial match)")
    insured_last_name: Optional[str] = Field(None, max_length=100, description="Insured last name (partial match)")
    policy_type: Optional[str] = Field(None, max_length=50, description="Policy type")
    loss_date: Optional[date] = Field(None, description="Date of loss")
    policy_city: Optional[str] = Field(None, max_length=100, description="Policy city (partial match)")
    policy_state: Optional[str] = Field(None, max_length=2, description="Policy state (2-letter code)")
    policy_zip: Optional[str] = Field(None, max_length=10, description="Policy ZIP code (partial match)")
    ssn_tin: Optional[str] = Field(None, min_length=9, max_length=11, description="SSN/TIN for search (will be hashed)")
    organizational_name: Optional[str] = Field(None, max_length=200, description="Organization name (partial match)")

    # Pagination and sorting
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Results per page")
    sort_by: Optional[str] = Field(default="policy_number", description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "insured_last_name": "Smith",
                "policy_state": "CA",
                "policy_type": "AUTO",
                "page": 1,
                "limit": 50
            }
        }
    )

    @field_validator("policy_state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        """Validate state code format."""
        if v is not None:
            return v.upper()
        return v

    @field_validator("ssn_tin")
    @classmethod
    def validate_ssn_tin(cls, v: Optional[str]) -> Optional[str]:
        """Clean SSN/TIN input."""
        if v is not None:
            # Remove all non-digits
            cleaned = ''.join(filter(str.isdigit, v))
            if len(cleaned) not in [9, 10]:  # SSN or EIN
                raise ValueError("SSN/TIN must be 9 or 10 digits")
            return cleaned
        return v


class VehicleDetails(BaseModel):
    """Vehicle details schema."""

    year: Optional[int] = Field(None, ge=1900, le=2030, description="Vehicle year")
    make: Optional[str] = Field(None, max_length=50, description="Vehicle make")
    model: Optional[str] = Field(None, max_length=50, description="Vehicle model")
    vin: Optional[str] = Field(None, max_length=17, description="Vehicle VIN")
    color: Optional[str] = Field(None, max_length=30, description="Vehicle color")
    license_plate: Optional[str] = Field(None, max_length=20, description="License plate")

    model_config = ConfigDict(str_strip_whitespace=True)


class CoverageDetails(BaseModel):
    """Coverage details schema."""

    liability: Optional[Dict[str, Any]] = Field(None, description="Liability coverage")
    comprehensive: Optional[Dict[str, Any]] = Field(None, description="Comprehensive coverage")
    collision: Optional[Dict[str, Any]] = Field(None, description="Collision coverage")
    uninsured_motorist: Optional[Dict[str, Any]] = Field(None, description="Uninsured motorist coverage")
    personal_injury: Optional[Dict[str, Any]] = Field(None, description="Personal injury protection")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "liability": {
                    "limit": 100000,
                    "deductible": 500
                },
                "comprehensive": {
                    "limit": 50000,
                    "deductible": 250
                }
            }
        }
    )


class PolicyCreate(BaseModel):
    """Policy creation request schema."""

    policy_number: str = Field(..., max_length=50, description="Unique policy number")
    policy_type: str = Field(..., max_length=50, description="Policy type")
    effective_date: date = Field(..., description="Policy effective date")
    expiration_date: date = Field(..., description="Policy expiration date")

    insured_first_name: str = Field(..., max_length=100, description="Insured first name")
    insured_last_name: str = Field(..., max_length=100, description="Insured last name")
    organizational_name: Optional[str] = Field(None, max_length=200, description="Organization name")
    ssn_tin: Optional[str] = Field(None, description="SSN/TIN (will be encrypted)")

    policy_address: Optional[str] = Field(None, max_length=255, description="Policy address")
    policy_city: str = Field(..., max_length=100, description="Policy city")
    policy_state: str = Field(..., max_length=2, description="Policy state")
    policy_zip: str = Field(..., max_length=10, description="Policy ZIP code")

    vehicle_details: Optional[VehicleDetails] = Field(None, description="Vehicle information")
    coverage_details: Optional[CoverageDetails] = Field(None, description="Coverage information")

    premium_amount: Optional[Decimal] = Field(None, ge=0, description="Premium amount")
    deductible_amount: Optional[Decimal] = Field(None, ge=0, description="Deductible amount")

    agent_id: Optional[str] = Field(None, max_length=50, description="Agent ID")
    underwriter: Optional[str] = Field(None, max_length=100, description="Underwriter")
    notes: Optional[str] = Field(None, description="Additional notes")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "policy_number": "POL123456789",
                "policy_type": "AUTO",
                "effective_date": "2024-01-01",
                "expiration_date": "2024-12-31",
                "insured_first_name": "John",
                "insured_last_name": "Doe",
                "policy_city": "Los Angeles",
                "policy_state": "CA",
                "policy_zip": "90210",
                "premium_amount": 1200.00
            }
        }
    )

    @field_validator("expiration_date")
    @classmethod
    def validate_expiration_after_effective(cls, v: date, info) -> date:
        """Validate expiration date is after effective date."""
        if info.data.get("effective_date") and v <= info.data["effective_date"]:
            raise ValueError("Expiration date must be after effective date")
        return v


class PolicyUpdate(BaseModel):
    """Policy update request schema."""

    policy_type: Optional[str] = Field(None, max_length=50)
    policy_status: Optional[str] = Field(None, max_length=20)
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None

    insured_first_name: Optional[str] = Field(None, max_length=100)
    insured_last_name: Optional[str] = Field(None, max_length=100)
    organizational_name: Optional[str] = Field(None, max_length=200)

    policy_address: Optional[str] = Field(None, max_length=255)
    policy_city: Optional[str] = Field(None, max_length=100)
    policy_state: Optional[str] = Field(None, max_length=2)
    policy_zip: Optional[str] = Field(None, max_length=10)

    vehicle_details: Optional[VehicleDetails] = None
    coverage_details: Optional[CoverageDetails] = None

    premium_amount: Optional[Decimal] = Field(None, ge=0)
    deductible_amount: Optional[Decimal] = Field(None, ge=0)

    agent_id: Optional[str] = Field(None, max_length=50)
    underwriter: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    model_config = ConfigDict(str_strip_whitespace=True)


class PolicyResponse(BaseModel):
    """Policy response schema with masked sensitive data."""

    id: uuid.UUID = Field(..., description="Policy ID")
    policy_number: str = Field(..., description="Policy number")
    policy_type: str = Field(..., description="Policy type")
    policy_status: str = Field(..., description="Policy status")
    effective_date: date = Field(..., description="Policy effective date")
    expiration_date: date = Field(..., description="Policy expiration date")

    insured_name: str = Field(..., description="Insured name (formatted)")
    organizational_name: Optional[str] = Field(None, description="Organization name")
    ssn_tin_masked: Optional[str] = Field(None, description="Masked SSN/TIN")

    policy_address: Optional[str] = Field(None, description="Policy address")
    policy_city: str = Field(..., description="Policy city")
    policy_state: str = Field(..., description="Policy state")
    policy_zip: str = Field(..., description="Policy ZIP code")
    full_address: str = Field(..., description="Formatted full address")

    vehicle_details: Optional[Dict[str, Any]] = Field(None, description="Vehicle information")
    coverage_details: Optional[Dict[str, Any]] = Field(None, description="Coverage information")

    premium_amount: Optional[Decimal] = Field(None, description="Premium amount")
    deductible_amount: Optional[Decimal] = Field(None, description="Deductible amount")

    agent_id: Optional[str] = Field(None, description="Agent ID")
    underwriter: Optional[str] = Field(None, description="Underwriter")

    is_active: bool = Field(..., description="Policy active status")
    is_expired: bool = Field(..., description="Policy expired status")
    days_until_expiration: int = Field(..., description="Days until expiration")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "policy_number": "POL123456789",
                "policy_type": "AUTO",
                "policy_status": "ACTIVE",
                "effective_date": "2024-01-01",
                "expiration_date": "2024-12-31",
                "insured_name": "John Doe",
                "ssn_tin_masked": "XXX-XX-1234",
                "policy_city": "Los Angeles",
                "policy_state": "CA",
                "policy_zip": "90210",
                "is_active": True,
                "is_expired": False
            }
        }
    )


class PolicySearchResponse(BaseModel):
    """Policy search response with pagination."""

    items: List[PolicyResponse] = Field(..., description="Policy search results")
    total_count: int = Field(..., description="Total number of matching policies")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")
    search_time_ms: int = Field(..., description="Search execution time in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total_count": 150,
                "page": 1,
                "limit": 50,
                "has_next": True,
                "has_previous": False,
                "search_time_ms": 234
            }
        }
    )


class PolicyWithClaimsResponse(PolicyResponse):
    """Policy response with associated claims."""

    claims: List["ClaimSummary"] = Field(default_factory=list, description="Associated claims")
    total_claims: int = Field(..., description="Total number of claims")
    open_claims: int = Field(..., description="Number of open claims")
    total_paid: Decimal = Field(..., description="Total amount paid on claims")

    model_config = ConfigDict(from_attributes=True)


# Import and rebuild for forward references
from app.schemas.claim import ClaimSummary
PolicyWithClaimsResponse.model_rebuild()