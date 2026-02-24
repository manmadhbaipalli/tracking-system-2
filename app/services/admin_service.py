import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole
from app.security import hash_password
from app.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)


async def list_users(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    active_only: bool = False,
) -> PaginatedResponse[UserResponse]:
    """List all users with pagination."""
    repo = UserRepository(session)
    total = await repo.count_users(active_only=active_only)
    users = await repo.list_users(limit=limit, offset=offset, active_only=active_only)
    items = [UserResponse.model_validate(u) for u in users]
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
    """Get a user by ID (admin access)."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")
    return user


async def update_user(
    session: AsyncSession,
    user_id: int,
    full_name: Optional[str] = None,
    role: Optional[UserRole] = None,
    active: Optional[bool] = None,
) -> User:
    """Update a user's profile (admin access)."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")

    updates = {}
    if full_name is not None:
        updates["full_name"] = full_name
    if role is not None:
        updates["role"] = role
    if active is not None:
        updates["active"] = active

    if updates:
        user = await repo.update_user(user_id, **updates)
        logger.info("Admin updated user: user_id=%d, updates=%s", user_id, list(updates.keys()))

    return user


async def create_user_as_admin(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.USER,
) -> User:
    """Create a user (admin access)."""
    repo = UserRepository(session)

    if await repo.email_exists(email):
        raise ConflictException(f"Email {email} is already registered")

    user = await repo.create_user(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        active=True,
    )
    logger.info("Admin created user: user_id=%d, email=%s, role=%s", user.id, user.email, role.value)
    return user


async def deactivate_user(
    session: AsyncSession,
    user_id: int,
    admin_user_id: int,
) -> User:
    """Deactivate (soft-delete) a user."""
    if user_id == admin_user_id:
        raise ForbiddenException("Cannot deactivate your own account")

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")

    user = await repo.update_user(user_id, active=False)
    logger.info("Admin deactivated user: user_id=%d, by_admin=%d", user_id, admin_user_id)
    return user
