from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user, require_admin
from app.schemas.user import UserResponse
from app.schemas.common import ErrorResponse, PageResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid token"},
        403: {"model": ErrorResponse, "description": "Account deactivated"},
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Return the profile of the currently authenticated user.

    Requires a valid JWT Bearer token in the `Authorization` header.
    """
    return UserResponse.model_validate(current_user)


@router.get(
    "",
    response_model=PageResponse[UserResponse],
    summary="List all users (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid token"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> PageResponse[UserResponse]:
    """
    List all users with pagination. Admin access required.

    - **page**: Page number starting from 1 (default: 1)
    - **page_size**: Number of items per page (default: 20, max: 100)
    """
    service = UserService(db)
    return await service.list_users(page=page, page_size=page_size)
