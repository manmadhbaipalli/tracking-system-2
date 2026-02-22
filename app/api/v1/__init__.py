"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth

# Create API v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Health check endpoint
@api_router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}