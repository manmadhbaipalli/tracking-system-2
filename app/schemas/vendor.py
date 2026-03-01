from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VendorCreate(BaseModel):
    vendor_name: str
    vendor_type: str
    tax_id: Optional[str] = None
    banking_info: Optional[dict] = None


class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = None
    vendor_type: Optional[str] = None
    payment_method_verified: Optional[bool] = None
    kyc_status: Optional[str] = None
    tax_id: Optional[str] = None
    banking_info: Optional[dict] = None
    stripe_account_id: Optional[str] = None


class VendorResponse(BaseModel):
    id: int
    vendor_name: str
    vendor_type: str
    payment_method_verified: bool
    kyc_status: str
    stripe_account_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VendorVerifyPaymentMethod(BaseModel):
    payment_method_type: str  # ach, wire, stripe
    verification_data: Optional[dict] = None
