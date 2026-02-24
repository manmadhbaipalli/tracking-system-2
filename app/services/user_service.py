import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.security import hash_password, verify_password
from app.exceptions import NotFoundException, AuthException

logger = logging.getLogger(__name__)


async def get_user_profile(session: AsyncSession, user_id: int) -> User:
    """Get a user's profile by ID."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")
    return user


async def update_user_profile(
    session: AsyncSession,
    user_id: int,
    full_name: Optional[str] = None,
) -> User:
    """Update a user's profile."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")

    updates = {}
    if full_name is not None:
        updates["full_name"] = full_name

    if updates:
        user = await repo.update_user(user_id, **updates)
        logger.info("User profile updated: user_id=%d", user_id)

    return user


async def change_password(
    session: AsyncSession,
    user_id: int,
    current_password: str,
    new_password: str,
) -> None:
    """Change a user's password after verifying the current password."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")

    if not verify_password(current_password, user.password_hash):
        raise AuthException("Current password is incorrect")

    new_hash = hash_password(new_password)
    await repo.update_user(user_id, password_hash=new_hash)
    logger.info("Password changed: user_id=%d", user_id)
