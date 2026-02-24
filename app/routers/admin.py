from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.security import get_current_user_id
from app.schemas.user import UserResponse
from app.schemas.admin import AdminUpdateUserRequest, AdminCreateUserRequest
from app.schemas.common import PaginatedResponse
from app.services.admin_service import (
    list_users, get_user_by_id, update_user, create_user_as_admin, deactivate_user,
)
from app.exceptions import ForbiddenException
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


async def require_admin(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Dependency that ensures the current user is an admin."""
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user_id)
    if not user or user.role != UserRole.ADMIN:
        raise ForbiddenException("Admin access required")
    return current_user_id


@router.get(
    "/users",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users",
    description="List all users with optional filtering and pagination (admin only).",
)
async def admin_list_users(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    active_only: bool = Query(default=False),
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await list_users(db, limit=limit, offset=offset, active_only=active_only)


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get a specific user by ID (admin only).",
)
async def admin_get_user(
    user_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_by_id(db, user_id)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user (admin)",
    description="Create a new user with specified role (admin only).",
)
async def admin_create_user(
    request: AdminCreateUserRequest,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await create_user_as_admin(
        db, request.email, request.password, request.full_name, request.role
    )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user (admin)",
    description="Update a user's profile, role, or active status (admin only).",
)
async def admin_update_user(
    user_id: int,
    request: AdminUpdateUserRequest,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await update_user(
        db, user_id,
        full_name=request.full_name,
        role=request.role,
        active=request.active,
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate user (admin)",
    description="Soft-delete a user by setting active=false (admin only).",
)
async def admin_deactivate_user(
    user_id: int,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await deactivate_user(db, user_id, admin_id)
