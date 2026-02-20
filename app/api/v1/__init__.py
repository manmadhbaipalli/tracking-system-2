"""API v1 router setup."""

from fastapi import APIRouter
from app.api.v1 import auth, users

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(users.router)