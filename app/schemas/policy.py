from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class PolicyCreate(BaseModel):
    policy_number: str
    insured_first_name: str
    insured_last_name: str
    organization_name: Optional[str] = None
    ssn_tin: Optional[str] = None
    policy_type: str
    effective_date: date
    expiration_date: date
    status: str = "active"
    vehicle_year: Optional[int] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_vin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    coverage_types: Optional[dict] = None
    coverage_limits: Optional[dict] = None
    coverage_deductibles: Optional[dict] = None


class PolicyUpdate(BaseModel):
    insured_first_name: Optional[str] = None
    insured_last_name: Optional[str] = None
    organization_name: Optional[str] = None
    policy_type: Optional[str] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_vin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    coverage_types: Optional[dict] = None
    coverage_limits: Optional[dict] = None
    coverage_deductibles: Optional[dict] = None


class PolicyResponse(BaseModel):
    id: int
    policy_number: str
    insured_first_name: str
    insured_last_name: str
    organization_name: Optional[str] = None
    ssn_tin_masked: Optional[str] = None  # Masked version
    policy_type: str
    effective_date: date
    expiration_date: date
    status: str
    vehicle_year: Optional[int] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_vin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    coverage_types: Optional[dict] = None
    coverage_limits: Optional[dict] = None
    coverage_deductibles: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicySearchParams(BaseModel):
    policy_number: Optional[str] = None
    insured_first_name: Optional[str] = None
    insured_last_name: Optional[str] = None
    organization_name: Optional[str] = None
    policy_type: Optional[str] = None
    loss_date: Optional[date] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    ssn_tin: Optional[str] = None
    page: int = Field(default=0, ge=0)
    size: int = Field(default=20, ge=1, le=100)
