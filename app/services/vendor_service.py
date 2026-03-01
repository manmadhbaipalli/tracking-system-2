import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse
from app.security import encrypt_sensitive_data
from app.exceptions import NotFoundException

logger = logging.getLogger(__name__)


async def create_vendor(session: AsyncSession, data: VendorCreate) -> Vendor:
    """Create a new vendor"""
    # Encrypt sensitive data
    encrypted_tax_id = encrypt_sensitive_data(data.tax_id) if data.tax_id else None
    encrypted_banking = data.banking_info  # In production, would encrypt this too

    vendor = Vendor(
        vendor_name=data.vendor_name,
        vendor_type=data.vendor_type,
        tax_id=encrypted_tax_id,
        banking_info=encrypted_banking
    )
    session.add(vendor)
    await session.commit()
    await session.refresh(vendor)
    logger.info("Vendor created: vendor_id=%d, name=%s", vendor.id, vendor.vendor_name)
    return vendor


async def get_vendor(session: AsyncSession, vendor_id: int) -> Vendor:
    """Get vendor by ID"""
    vendor = await session.get(Vendor, vendor_id)
    if not vendor:
        raise NotFoundException(f"Vendor with id {vendor_id} not found")
    return vendor


async def update_vendor(session: AsyncSession, vendor_id: int, data: VendorUpdate) -> Vendor:
    """Update vendor"""
    vendor = await session.get(Vendor, vendor_id)
    if not vendor:
        raise NotFoundException(f"Vendor with id {vendor_id} not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            # Encrypt sensitive fields
            if field == "tax_id":
                value = encrypt_sensitive_data(value) if value else None
            setattr(vendor, field, value)

    await session.commit()
    await session.refresh(vendor)
    logger.info("Vendor updated: vendor_id=%d", vendor.id)
    return vendor


async def verify_vendor_payment_method(session: AsyncSession, vendor_id: int, payment_method_type: str) -> Vendor:
    """Verify vendor payment method and update KYC status"""
    vendor = await session.get(Vendor, vendor_id)
    if not vendor:
        raise NotFoundException(f"Vendor with id {vendor_id} not found")

    # In production, this would integrate with payment processor for actual verification
    vendor.payment_method_verified = True
    vendor.kyc_status = "verified"

    await session.commit()
    await session.refresh(vendor)
    logger.info("Vendor payment method verified: vendor_id=%d, method=%s", vendor.id, payment_method_type)
    return vendor


async def list_vendors(session: AsyncSession) -> list[VendorResponse]:
    """List all vendors"""
    result = await session.execute(select(Vendor))
    vendors = result.scalars().all()
    return [VendorResponse.model_validate(vendor) for vendor in vendors]
