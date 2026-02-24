"""Claims request/response schemas with policy linking, audit trail data, and status filtering."""

import uuid
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.models.claim import ClaimStatus, ClaimType


class ClaimCreate(BaseModel):
    """Claim creation request schema."""

    claim_number: str = Field(..., max_length=50)
    policy_id: uuid.UUID = Field(...)
    claim_type: ClaimType = Field(...)
    date_of_loss: date = Field(...)
    claim_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    location_of_loss: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class ClaimUpdate(BaseModel):
    """Claim update request schema."""

    claim_status: Optional[ClaimStatus] = None
    claim_amount: Optional[Decimal] = Field(None, ge=0)
    reserve_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    adjuster_id: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(str_strip_whitespace=True)


class ClaimResponse(BaseModel):
    """Claim response schema."""

    id: uuid.UUID
    claim_number: str
    policy_id: uuid.UUID
    claim_type: ClaimType
    claim_status: ClaimStatus
    date_of_loss: date
    claim_amount: Optional[Decimal]
    paid_amount: Decimal
    is_open: bool
    days_since_loss: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimSummary(BaseModel):
    """Claim summary for policy responses."""

    id: uuid.UUID
    claim_number: str
    claim_status: ClaimStatus
    date_of_loss: date
    claim_amount: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)


class ClaimHistoryItem(BaseModel):
    """Claim history item schema."""

    claim_number: str
    date_of_loss: date
    claim_status: ClaimStatus
    claim_amount: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)


class ClaimSearchRequest(BaseModel):
    """Claim search request schema."""

    policy_id: Optional[uuid.UUID] = None
    claim_status: Optional[ClaimStatus] = None
    claim_type: Optional[ClaimType] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(str_strip_whitespace=True)


class ClaimHistoryResponse(BaseModel):
    """Claim history response schema."""

    claims: List[ClaimHistoryItem]
    total_count: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)