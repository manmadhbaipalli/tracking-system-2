from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class ClaimCreate(BaseModel):
    claim_number: str
    policy_id: int
    loss_date: date
    claim_status: str = "open"
    description: Optional[str] = None
    claim_level_policy_data: Optional[dict] = None
    injury_incident_details: Optional[dict] = None
    coding_information: Optional[dict] = None
    carrier_involvement: Optional[dict] = None


class ClaimUpdate(BaseModel):
    claim_status: Optional[str] = None
    description: Optional[str] = None
    claim_level_policy_data: Optional[dict] = None
    injury_incident_details: Optional[dict] = None
    coding_information: Optional[dict] = None
    carrier_involvement: Optional[dict] = None
    referred_to_subrogation: Optional[bool] = None
    scheduled_payment_applicable: Optional[bool] = None
    scheduled_payment_type: Optional[str] = None
    scheduled_payment_total: Optional[Decimal] = None
    scheduled_payment_balance: Optional[Decimal] = None
    scheduled_payment_current_due: Optional[Decimal] = None
    scheduled_payment_recipient: Optional[str] = None


class ClaimResponse(BaseModel):
    id: int
    claim_number: str
    policy_id: int
    loss_date: date
    claim_status: str
    description: Optional[str] = None
    claim_level_policy_data: Optional[dict] = None
    injury_incident_details: Optional[dict] = None
    coding_information: Optional[dict] = None
    carrier_involvement: Optional[dict] = None
    referred_to_subrogation: bool
    subrogation_date: Optional[date] = None
    scheduled_payment_applicable: bool
    scheduled_payment_type: Optional[str] = None
    scheduled_payment_total: Optional[Decimal] = None
    scheduled_payment_balance: Optional[Decimal] = None
    scheduled_payment_current_due: Optional[Decimal] = None
    scheduled_payment_recipient: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClaimSearchParams(BaseModel):
    claim_number: Optional[str] = None
    policy_id: Optional[int] = None
    claim_status: Optional[str] = None
    loss_date_from: Optional[date] = None
    loss_date_to: Optional[date] = None
    page: int = Field(default=0, ge=0)
    size: int = Field(default=20, ge=1, le=100)


class ClaimPolicyDataUpdate(BaseModel):
    claim_level_policy_data: dict


class SubrogationReferral(BaseModel):
    referral_notes: Optional[str] = None
