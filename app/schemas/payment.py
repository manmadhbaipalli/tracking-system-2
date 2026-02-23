"""Payment request/response schemas with multiple payment methods and compliance data masking."""

import uuid
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.models.payment import PaymentStatus, PaymentMethod, PaymentType


class PayeeCreate(BaseModel):
    """Payee creation schema."""

    payee_type: str = Field(..., max_length=20)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    business_name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class PaymentCreate(BaseModel):
    """Payment creation request schema."""

    claim_id: Optional[uuid.UUID] = None
    payment_type: PaymentType = Field(...)
    payment_method: PaymentMethod = Field(...)
    total_amount: Decimal = Field(..., gt=0)
    payment_memo: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(str_strip_whitespace=True)


class PaymentUpdate(BaseModel):
    """Payment update request schema."""

    payment_status: Optional[PaymentStatus] = None
    payment_date: Optional[date] = None
    payment_memo: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(str_strip_whitespace=True)


class PaymentResponse(BaseModel):
    """Payment response schema with masked sensitive data."""

    id: uuid.UUID
    payment_number: str
    claim_id: Optional[uuid.UUID]
    payment_type: PaymentType
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    total_amount: Decimal
    net_amount: Decimal
    is_processed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)