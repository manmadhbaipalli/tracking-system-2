"""
Claims Service Platform - Policy Schemas

Pydantic schemas for policy create/update/response validation with proper field masking.
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal


class PolicySearchRequest(BaseModel):
    """Policy search request schema with multiple criteria support"""
    policy_number: Optional[str] = Field(None, max_length=20)
    insured_first_name: Optional[str] = Field(None, max_length=100)
    insured_last_name: Optional[str] = Field(None, max_length=100)
    policy_type: Optional[str] = Field(None, max_length=50)
    loss_date_from: Optional[date]
    loss_date_to: Optional[date]
    effective_date_from: Optional[date]
    effective_date_to: Optional[date]
    policy_city: Optional[str] = Field(None, max_length=100)
    policy_state: Optional[str] = Field(None, max_length=2)
    policy_zip: Optional[str] = Field(None, max_length=10)
    ssn_tin: Optional[str] = Field(None, max_length=11)
    organization_name: Optional[str] = Field(None, max_length=200)
    search_type: str = Field("exact", pattern="^(exact|partial)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(policy_number|insured_last_name|effective_date|created_at|updated_at)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

    @validator('policy_state')
    def validate_state_code(cls, v):
        if v:
            from app.utils.validators import validate_state_code
            validate_state_code(v)
        return v.upper() if v else v

    @validator('policy_zip')
    def validate_zip_code(cls, v):
        if v:
            from app.utils.validators import validate_zip_code
            validate_zip_code(v)
        return v

    @validator('loss_date_to')
    def validate_date_range(cls, v, values):
        if v and 'loss_date_from' in values and values['loss_date_from']:
            if v < values['loss_date_from']:
                raise ValueError('loss_date_to cannot be before loss_date_from')
        return v

    @validator('effective_date_to')
    def validate_effective_date_range(cls, v, values):
        if v and 'effective_date_from' in values and values['effective_date_from']:
            if v < values['effective_date_from']:
                raise ValueError('effective_date_to cannot be before effective_date_from')
        return v


class CoverageDetails(BaseModel):
    """Coverage details schema"""
    type: str = Field(..., max_length=50)
    limit: Decimal = Field(..., ge=0)
    deductible: Decimal = Field(default=0, ge=0)
    premium: Decimal = Field(default=0, ge=0)
    effective_date: Optional[date]
    description: Optional[str] = Field(None, max_length=200)


class PolicyCreate(BaseModel):
    """Policy creation schema"""
    policy_number: str = Field(..., min_length=8, max_length=20)
    policy_type: str = Field(..., max_length=50)
    effective_date: date
    expiration_date: date
    insured_first_name: str = Field(..., min_length=1, max_length=100)
    insured_last_name: str = Field(..., min_length=1, max_length=100)
    ssn: Optional[str] = Field(None, max_length=11)
    tin: Optional[str] = Field(None, max_length=11)
    organization_name: Optional[str] = Field(None, max_length=200)
    organization_type: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    mobile_phone: Optional[str] = Field(None, max_length=20)
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)
    country: str = Field(default="USA", max_length=3)
    premium_amount: Optional[Decimal] = Field(None, ge=0)
    deductible_amount: Optional[Decimal] = Field(None, ge=0)
    policy_limit: Optional[Decimal] = Field(None, ge=0)
    vehicle_year: Optional[int] = Field(None, ge=1900, le=2030)
    vehicle_make: Optional[str] = Field(None, max_length=50)
    vehicle_model: Optional[str] = Field(None, max_length=50)
    vehicle_vin: Optional[str] = Field(None, max_length=17)
    vehicle_color: Optional[str] = Field(None, max_length=30)
    vehicle_license_plate: Optional[str] = Field(None, max_length=20)
    coverage_details: Optional[List[CoverageDetails]] = []
    agent_name: Optional[str] = Field(None, max_length=100)
    agent_code: Optional[str] = Field(None, max_length=20)
    branch_code: Optional[str] = Field(None, max_length=20)
    underwriter: Optional[str] = Field(None, max_length=100)

    @validator('policy_number')
    def validate_policy_number(cls, v):
        from app.utils.validators import validate_policy_number
        validate_policy_number(v)
        return v.upper()

    @validator('ssn')
    def validate_ssn_format(cls, v):
        if v:
            from app.utils.validators import validate_ssn
            validate_ssn(v)
        return v

    @validator('tin')
    def validate_tin_format(cls, v):
        if v:
            from app.utils.validators import validate_tin
            validate_tin(v)
        return v

    @validator('state')
    def validate_state_code(cls, v):
        from app.utils.validators import validate_state_code
        validate_state_code(v)
        return v.upper()

    @validator('zip_code')
    def validate_zip_code(cls, v):
        from app.utils.validators import validate_zip_code
        validate_zip_code(v)
        return v

    @validator('vehicle_vin')
    def validate_vin_format(cls, v):
        if v:
            from app.utils.validators import validate_vin
            validate_vin(v)
        return v.upper() if v else v

    @validator('expiration_date')
    def validate_policy_dates(cls, v, values):
        if v and 'effective_date' in values and values['effective_date']:
            if v <= values['effective_date']:
                raise ValueError('Expiration date must be after effective date')
        return v

    @validator('email')
    def validate_email_format(cls, v):
        if v:
            from app.utils.validators import validate_email
            validate_email(v)
        return v

    @validator('phone')
    def validate_phone_format(cls, v):
        if v:
            from app.utils.validators import validate_phone
            validate_phone(v)
        return v


class PolicyUpdate(BaseModel):
    """Policy update schema"""
    policy_type: Optional[str] = Field(None, max_length=50)
    effective_date: Optional[date]
    expiration_date: Optional[date]
    insured_first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    insured_last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    organization_name: Optional[str] = Field(None, max_length=200)
    organization_type: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    mobile_phone: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, min_length=1, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(None, min_length=5, max_length=10)
    premium_amount: Optional[Decimal] = Field(None, ge=0)
    deductible_amount: Optional[Decimal] = Field(None, ge=0)
    policy_limit: Optional[Decimal] = Field(None, ge=0)
    vehicle_year: Optional[int] = Field(None, ge=1900, le=2030)
    vehicle_make: Optional[str] = Field(None, max_length=50)
    vehicle_model: Optional[str] = Field(None, max_length=50)
    vehicle_color: Optional[str] = Field(None, max_length=30)
    vehicle_license_plate: Optional[str] = Field(None, max_length=20)
    coverage_details: Optional[List[CoverageDetails]]
    agent_name: Optional[str] = Field(None, max_length=100)
    agent_code: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)

    @validator('state')
    def validate_state_code(cls, v):
        if v:
            from app.utils.validators import validate_state_code
            validate_state_code(v)
        return v.upper() if v else v

    @validator('zip_code')
    def validate_zip_code(cls, v):
        if v:
            from app.utils.validators import validate_zip_code
            validate_zip_code(v)
        return v

    @validator('email')
    def validate_email_format(cls, v):
        if v:
            from app.utils.validators import validate_email
            validate_email(v)
        return v

    @validator('phone')
    def validate_phone_format(cls, v):
        if v:
            from app.utils.validators import validate_phone
            validate_phone(v)
        return v


class PolicyResponse(BaseModel):
    """Policy response schema with masked PII fields"""
    id: int
    policy_number: str
    policy_type: str
    status: str
    effective_date: date
    expiration_date: date
    loss_date: Optional[date]
    insured_first_name: str
    insured_last_name: str
    insured_full_name: str
    ssn: Optional[str]  # Will be masked
    tin: Optional[str]  # Will be masked
    organization_name: Optional[str]
    organization_type: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    mobile_phone: Optional[str]
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    zip_code: str
    country: str
    premium_amount: Optional[Decimal]
    deductible_amount: Optional[Decimal]
    policy_limit: Optional[Decimal]
    vehicle_year: Optional[int]
    vehicle_make: Optional[str]
    vehicle_model: Optional[str]
    vehicle_vin: Optional[str]
    vehicle_color: Optional[str]
    vehicle_license_plate: Optional[str]
    coverage_details: Optional[List[Dict[str, Any]]]
    coverage_limits: Optional[Dict[str, Any]]
    deductibles: Optional[Dict[str, Any]]
    agent_name: Optional[str]
    agent_code: Optional[str]
    branch_code: Optional[str]
    underwriter: Optional[str]
    risk_score: Optional[int]
    is_active: bool
    days_until_expiration: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class PolicySummary(BaseModel):
    """Policy summary for search results"""
    id: int
    policy_number: str
    policy_type: str
    status: str
    insured_full_name: str
    effective_date: date
    expiration_date: date
    city: str
    state: str
    is_active: bool

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class PolicySearchResponse(BaseModel):
    """Policy search response with pagination"""
    policies: List[PolicySummary]
    total: int
    page: int
    page_size: int
    total_pages: int
    search_criteria: Dict[str, Any]


class PolicyAuditResponse(BaseModel):
    """Policy audit history response"""
    policy_id: int
    audit_logs: List[Dict[str, Any]]
    total_changes: int


class PolicyClaimsHistoryResponse(BaseModel):
    """Policy claims history response"""
    policy_id: int
    claims: List[Dict[str, Any]]
    total_claims: int
    open_claims: int
    total_paid: Decimal
    total_outstanding: Decimal

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PolicyValidationRequest(BaseModel):
    """Policy validation request"""
    policy_number: str
    effective_date: date
    expiration_date: date


class PolicyValidationResponse(BaseModel):
    """Policy validation response"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class BulkPolicyOperation(BaseModel):
    """Bulk policy operation request"""
    policy_ids: List[int] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., pattern="^(activate|deactivate|expire|cancel)$")
    reason: Optional[str] = Field(None, max_length=500)


class BulkPolicyOperationResponse(BaseModel):
    """Bulk policy operation response"""
    successful: List[int]
    failed: List[Dict[str, Any]]
    total_processed: int
    success_count: int
    failure_count: int