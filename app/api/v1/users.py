"""User management endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.security import get_current_user
from app.core.logging import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger("app.api.users")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user's profile.

    Args:
        current_user: Current authenticated user from JWT token
        db: Database session

    Returns:
        User profile information
    """
    logger.info(f"Profile request for user ID: {current_user.id}")

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )