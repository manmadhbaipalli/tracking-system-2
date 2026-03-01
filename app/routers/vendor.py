from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorVerifyPaymentMethod
from app.services import vendor_service
from app.security import get_current_user_id

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(
    data: VendorCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Create/onboard a new vendor"""
    vendor = await vendor_service.create_vendor(session, data)
    return VendorResponse.model_validate(vendor)


@router.get("", response_model=list[VendorResponse])
async def list_vendors(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """List all vendors"""
    return await vendor_service.list_vendors(session)


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get vendor details"""
    vendor = await vendor_service.get_vendor(session, vendor_id)
    return VendorResponse.model_validate(vendor)


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Update vendor"""
    vendor = await vendor_service.update_vendor(session, vendor_id, data)
    return VendorResponse.model_validate(vendor)


@router.post("/{vendor_id}/verify-payment-method", response_model=VendorResponse)
async def verify_payment_method(
    vendor_id: int,
    data: VendorVerifyPaymentMethod,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Verify vendor payment method"""
    vendor = await vendor_service.verify_vendor_payment_method(session, vendor_id, data.payment_method_type)
    return VendorResponse.model_validate(vendor)
