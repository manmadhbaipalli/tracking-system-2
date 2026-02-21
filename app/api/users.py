"""User management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import logging

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserResponse, UserUpdate
from ..core.auth import get_current_user
from ..core.exceptions import (
    DatabaseError,
    UserAlreadyExistsError,
    ValidationError
)

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user's profile.

    Args:
        current_user: Current authenticated user from JWT

    Returns:
        UserResponse: User profile data
    """
    logger.info(f"Profile request for user: {current_user.id}")

    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the authenticated user's profile information"
)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update current authenticated user's profile.

    Args:
        user_update: User update data
        current_user: Current authenticated user from JWT
        db: Database session

    Returns:
        UserResponse: Updated user profile data

    Raises:
        UserAlreadyExistsError: If email is already taken by another user
        ValidationError: If update data is invalid
        DatabaseError: If database operation fails
    """
    logger.info(f"Profile update request for user: {current_user.id}")

    try:
        # Track if any changes were made
        changes_made = False

        # Update email if provided
        if user_update.email is not None and user_update.email != current_user.email:
            # Check if email is already taken by another user
            stmt = select(User).where(
                User.email == user_update.email,
                User.id != current_user.id
            )
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.warning(
                    f"Email update failed - email already exists: {user_update.email}"
                )
                raise UserAlreadyExistsError(
                    message="Email address is already taken by another user",
                    details={"email": user_update.email}
                )

            current_user.email = user_update.email
            changes_made = True
            logger.info(f"Email updated for user {current_user.id}: {user_update.email}")

        # Update is_active if provided (admin functionality)
        if user_update.is_active is not None and user_update.is_active != current_user.is_active:
            current_user.is_active = user_update.is_active
            changes_made = True
            logger.info(f"Active status updated for user {current_user.id}: {user_update.is_active}")

        # Commit changes if any were made
        if changes_made:
            await db.commit()
            await db.refresh(current_user)
            logger.info(f"Profile updated successfully for user: {current_user.id}")
        else:
            logger.info(f"No changes made to user profile: {current_user.id}")

        return UserResponse.model_validate(current_user)

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during profile update: {e}")
        raise UserAlreadyExistsError(
            message="Email address is already taken by another user",
            details={"email": user_update.email}
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during profile update: {e}")
        raise DatabaseError(
            message="Failed to update user profile",
            details={"error": str(e)}
        )


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Deactivate current user account",
    description="Deactivate the authenticated user's account (soft delete)"
)
async def deactivate_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Deactivate current authenticated user's account.

    This performs a soft delete by setting is_active to False.

    Args:
        current_user: Current authenticated user from JWT
        db: Database session

    Returns:
        dict: Success message

    Raises:
        DatabaseError: If database operation fails
    """
    logger.info(f"Account deactivation request for user: {current_user.id}")

    try:
        # Set user as inactive
        current_user.is_active = False

        await db.commit()
        await db.refresh(current_user)

        logger.info(f"User account deactivated: {current_user.id}")

        return {
            "message": "User account has been deactivated",
            "detail": "Your account has been deactivated. Contact support to reactivate."
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during account deactivation: {e}")
        raise DatabaseError(
            message="Failed to deactivate user account",
            details={"error": str(e)}
        )