"""
Claims Service Platform - Claim Schemas

Pydantic schemas for claims with policy relationship validation and claim-level policy overrides.
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal


class ClaimCreate(BaseModel):
    """Claim creation schema"""
    claim_number: str = Field(..., min_length=8, max_length=25)
    policy_id: int
    claim_type: str = Field(..., max_length=50)
    date_of_loss: date
    date_reported: date = Field(default_factory=date.today)
    loss_description: str = Field(..., min_length=10, max_length=2000)
    loss_cause: Optional[str] = Field(None, max_length=100)
    loss_location: Optional[str] = Field(None, max_length=500)
    police_report_number: Optional[str] = Field(None, max_length=50)
    reserve_amount: Decimal = Field(default=0, ge=0)
    claimant_name: Optional[str] = Field(None, max_length=200)
    adjuster_id: Optional[int]

    @validator('claim_number')
    def validate_claim_number(cls, v):
        from app.utils.validators import validate_claim_number
        validate_claim_number(v)
        return v.upper()

    @validator('date_reported')
    def validate_reported_date(cls, v, values):
        if v and 'date_of_loss' in values and values['date_of_loss']:
            if v < values['date_of_loss']:
                raise ValueError('Date reported cannot be before date of loss')
        return v


class ClaimUpdate(BaseModel):
    """Claim update schema"""
    status: Optional[str] = Field(None, max_length=20)
    loss_description: Optional[str] = Field(None, max_length=2000)
    reserve_amount: Optional[Decimal] = Field(None, ge=0)
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    adjuster_id: Optional[int]
    claim_policy_data: Optional[Dict[str, Any]]
    investigation_notes: Optional[str]


class ClaimResponse(BaseModel):
    """Claim response schema"""
    id: int
    claim_number: str
    policy_id: int
    claim_type: str
    status: str
    severity: Optional[str]
    date_of_loss: date
    date_reported: date
    date_closed: Optional[date]
    loss_description: str
    reserve_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    claimant_name: Optional[str]
    adjuster_name: Optional[str]
    has_claim_level_policy_data: bool
    days_open: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class ClaimListResponse(BaseModel):
    """Claim list response with filtering"""
    claims: List[ClaimResponse]
    total: int
    page: int
    page_size: int
    total_pages: int