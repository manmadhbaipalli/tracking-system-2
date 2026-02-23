"""User management endpoints for profile operations."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.circuit_breaker import circuit_breaker
from app.core.security import get_current_active_user, hash_password
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Get current user's profile information.

    Args:
        current_user: Currently authenticated user

    Returns:
        UserResponse: User profile information
    """
    logger.info("User profile accessed", user_id=str(current_user.id))
    return UserResponse.model_validate(current_user)


@circuit_breaker("user_profile_update", failure_threshold=5, recovery_timeout=30)
async def update_user_in_db(
    db: AsyncSession, user: User, update_data: UserUpdate
) -> User:
    """
    Update user information in database with circuit breaker protection.

    Args:
        db: Database session
        user: User to update
        update_data: Update data

    Returns:
        User: Updated user object
    """
    # Update fields if provided
    if update_data.email is not None:
        user.email = update_data.email

    if update_data.password is not None:
        user.hashed_password = await hash_password(update_data.password)

    if update_data.is_active is not None:
        user.is_active = update_data.is_active

    try:
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Update current user's profile information.

    Args:
        update_data: Fields to update
        db: Database session
        current_user: Currently authenticated user

    Returns:
        UserResponse: Updated user profile information

    Raises:
        HTTPException: If update fails
    """
    try:
        logger.info("User profile update attempt", user_id=str(current_user.id))

        # Check if there's anything to update
        if not any([
            update_data.email is not None,
            update_data.password is not None,
            update_data.is_active is not None,
        ]):
            logger.info("No fields to update", user_id=str(current_user.id))
            return UserResponse.model_validate(current_user)

        updated_user = await update_user_in_db(db, current_user, update_data)
        logger.info("User profile updated successfully", user_id=str(updated_user.id))

        return UserResponse.model_validate(updated_user)

    except Exception as e:
        logger.error("Profile update failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@circuit_breaker("user_account_deletion", failure_threshold=5, recovery_timeout=30)
async def delete_user_from_db(db: AsyncSession, user: User) -> None:
    """
    Delete user from database with circuit breaker protection.

    Args:
        db: Database session
        user: User to delete
    """
    try:
        await db.delete(user)
        await db.commit()
    except Exception:
        await db.rollback()
        raise


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete current user's account permanently.

    Args:
        db: Database session
        current_user: Currently authenticated user

    Raises:
        HTTPException: If deletion fails
    """
    try:
        logger.info("User account deletion attempt", user_id=str(current_user.id))
        await delete_user_from_db(db, current_user)
        logger.info("User account deleted successfully", user_id=str(current_user.id))

    except Exception as e:
        logger.error("Account deletion failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.get("/me/health")
async def get_user_health_check(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Health check endpoint for authenticated users.

    Args:
        current_user: Currently authenticated user

    Returns:
        Dict[str, Any]: Health check information
    """
    return {
        "status": "healthy",
        "user_id": str(current_user.id),
        "is_active": current_user.is_active,
        "authenticated": True,
    }