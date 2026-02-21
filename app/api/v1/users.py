"""User management endpoints for profile access."""
import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current user profile."""
    logger.info(f"User profile accessed: {current_user.email}")
    return UserResponse.model_validate(current_user)