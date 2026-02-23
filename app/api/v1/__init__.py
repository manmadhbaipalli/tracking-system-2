"""
API version 1 routes for the insurance management system.

Provides REST endpoints for:
- /auth - Authentication and user management
- /policies - Policy management and search
- /claims - Claims processing and history
- /payments - Payment processing and lifecycle
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.policies import router as policies_router
from app.api.v1.claims import router as claims_router
from app.api.v1.payments import router as payments_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(policies_router, prefix="/policies", tags=["policies"])
api_router.include_router(claims_router, prefix="/claims", tags=["claims"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])