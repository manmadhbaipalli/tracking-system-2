from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserResponse
from app.schemas.admin import RoleUpdateRequest, StatusUpdateRequest
from app.schemas.common import PageResponse

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/users", response_model=PageResponse[UserResponse],
            summary="List all users (paginated)")
def list_users(
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
):
    """
    List all users with pagination.

    Returns a paginated list of all users in the system.
    Requires ADMIN role.

    NOTE: Admin auth dependency will be implemented by the dev agent.
    """
    # Service layer and admin auth dependency will be implemented by the dev agent
    from app.services.admin_service import list_all_users
    return list_all_users(db, page=page, size=size)


@router.put("/users/{user_id}/role", response_model=UserResponse,
            summary="Update user role",
            responses={
                404: {"description": "User not found"},
                400: {"description": "Validation error"}
            })
def update_user_role(user_id: int, request: RoleUpdateRequest, db: Session = Depends(get_db)):
    """
    Update a user's role (USER or ADMIN).

    Allows promoting users to ADMIN or demoting them to USER.
    Requires ADMIN role.

    NOTE: Admin auth dependency will be implemented by the dev agent.
    """
    # Service layer and admin auth dependency will be implemented by the dev agent
    from app.services.admin_service import update_user_role
    return update_user_role(db, user_id, request)


@router.put("/users/{user_id}/status", response_model=UserResponse,
            summary="Update user active status",
            responses={
                404: {"description": "User not found"},
                400: {"description": "Cannot deactivate yourself"}
            })
def update_user_status(user_id: int, request: StatusUpdateRequest, db: Session = Depends(get_db)):
    """
    Activate or deactivate a user account.

    Allows admins to enable/disable user accounts.
    Prevents self-deactivation to avoid lockout.
    Requires ADMIN role.

    NOTE: Admin auth dependency will be implemented by the dev agent.
    """
    # Service layer and admin auth dependency will be implemented by the dev agent
    from app.services.admin_service import update_user_status
    # current_admin_id will come from auth dependency to prevent self-deactivation
    current_admin_id = 1  # Placeholder - admin auth dependency will provide this
    return update_user_status(db, user_id, request, current_admin_id)