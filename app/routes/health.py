"""Health check endpoint for monitoring and load balancer checks."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", status_code=200)
async def health_check() -> dict:
    """
    Health check endpoint.

    Used by load balancers and monitoring systems to verify service is running.
    Returns 200 if healthy.
    """
    return {"status": "healthy"}
