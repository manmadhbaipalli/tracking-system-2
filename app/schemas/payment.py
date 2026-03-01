from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class PaymentDetailCreate(BaseModel):
    payee_type: str
    payee_id: Optional[int] = None
    payee_name: str
    payment_portion: Decimal
    deduction_amount: Optional[Decimal] = None
    deduction_reason: Optional[str] = None
    banking_info: Optional[dict] = None


class PaymentDetailResponse(BaseModel):
    id: int
    payment_id: int
    payee_type: str
    payee_id: Optional[int] = None
    payee_name: str
    payment_portion: Decimal
    deduction_amount: Optional[Decimal] = None
    deduction_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    payment_number: str
    claim_id: int
    policy_id: int
    payment_method: str
    payment_type: str
    total_amount: Decimal
    is_eroding: bool = True
    reserve_lines: Optional[dict] = None
    is_tax_reportable: bool = False
    tax_id_number: Optional[str] = None
    payment_details: Optional[List[PaymentDetailCreate]] = None


class PaymentUpdate(BaseModel):
    payment_method: Optional[str] = None
    payment_type: Optional[str] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None
    is_eroding: Optional[bool] = None
    reserve_lines: Optional[dict] = None
    is_tax_reportable: Optional[bool] = None
    tax_id_number: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    payment_number: str
    claim_id: int
    policy_id: int
    payment_method: str
    payment_type: str
    total_amount: Decimal
    status: str
    is_eroding: bool
    reserve_lines: Optional[dict] = None
    is_tax_reportable: bool
    payment_date: Optional[date] = None
    void_date: Optional[date] = None
    void_reason: Optional[str] = None
    reversal_date: Optional[date] = None
    reversal_reason: Optional[str] = None
    reissue_date: Optional[date] = None
    original_payment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentSearchParams(BaseModel):
    payment_number: Optional[str] = None
    claim_id: Optional[int] = None
    policy_id: Optional[int] = None
    status: Optional[str] = None
    payment_method: Optional[str] = None
    page: int = Field(default=0, ge=0)
    size: int = Field(default=20, ge=1, le=100)


class PaymentVoid(BaseModel):
    void_reason: str


class PaymentReverse(BaseModel):
    reversal_reason: str


class PaymentReissue(BaseModel):
    notes: Optional[str] = None
