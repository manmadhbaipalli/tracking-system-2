# Export all routers
from app.routers.auth import router as auth_router
from app.routers.policy import router as policy_router
from app.routers.claim import router as claim_router
from app.routers.payment import router as payment_router
from app.routers.vendor import router as vendor_router

__all__ = [
    "auth_router",
    "policy_router",
    "claim_router",
    "payment_router",
    "vendor_router",
]
