"""
Claims Service Platform - Payment Schemas

Pydantic schemas for payment processing with sensitive data validation and compliance.
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal


class PaymentCreate(BaseModel):
    """Payment creation schema"""
    claim_id: int
    payment_method: str = Field(..., pattern="^(ach|wire|check|card|stripe_connect)$")
    payment_type: str = Field(..., max_length=50)
    amount: Decimal = Field(..., ge=-999999999.99, le=999999999.99)
    currency: str = Field(default="USD", max_length=3)
    payment_date: date = Field(default_factory=date.today)
    payee_name: str = Field(..., min_length=1, max_length=200)
    payee_type: Optional[str] = Field(None, max_length=50)
    payee_address: Optional[Dict[str, Any]]
    bank_name: Optional[str] = Field(None, max_length=100)
    routing_number: Optional[str] = Field(None, max_length=9)
    account_number: Optional[str] = Field(None, max_length=20)
    account_type: Optional[str] = Field(None, pattern="^(checking|savings)$")
    is_tax_reportable: bool = Field(default=False)
    withholding_amount: Decimal = Field(default=0, ge=0)
    reserve_allocations: Optional[List[Dict[str, Any]]] = []

    @validator('amount')
    def validate_payment_amount(cls, v):
        from app.utils.validators import validate_payment_amount
        validate_payment_amount(v)
        return v

    @validator('routing_number')
    def validate_routing_number(cls, v):
        if v:
            from app.utils.validators import validate_routing_number
            validate_routing_number(v)
        return v


class PaymentUpdate(BaseModel):
    """Payment update schema"""
    status: Optional[str] = Field(None, max_length=20)
    processed_date: Optional[date]
    failure_reason: Optional[str] = Field(None, max_length=500)
    approval_notes: Optional[str]


class PaymentResponse(BaseModel):
    """Payment response schema"""
    id: int
    payment_number: str
    claim_id: int
    payment_method: str
    payment_type: str
    status: str
    amount: Decimal
    currency: str
    payment_date: date
    payee_name: str
    bank_name: Optional[str]
    routing_number: Optional[str]  # Will be masked
    account_number: Optional[str]  # Will be masked
    is_tax_reportable: bool
    withholding_amount: Decimal
    net_amount: Decimal
    requires_approval: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }