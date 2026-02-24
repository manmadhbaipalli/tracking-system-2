from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdateRequest, PasswordChangeRequest

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=UserResponse,
            summary="Get current user profile")
def get_current_user(db: Session = Depends(get_db)):
    """
    Get the profile of the currently authenticated user.

    Returns user information including email, full name, role, and account status.
    Requires valid JWT token in Authorization header.

    NOTE: Auth dependency (get_current_user_id) will be implemented by the dev agent.
    """
    # Service layer and auth dependency will be implemented by the dev agent
    from app.services.user_service import get_user_by_id
    # current_user_id will come from auth dependency
    current_user_id = 1  # Placeholder - auth dependency will provide this
    return get_user_by_id(db, current_user_id)


@router.put("/me", response_model=UserResponse,
            summary="Update current user profile",
            responses={
                409: {"description": "Email already exists"},
                400: {"description": "Validation error"}
            })
def update_current_user(
    request: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update the profile of the currently authenticated user.

    Can update full name and email. Email must be unique if changed.
    Requires valid JWT token in Authorization header.

    NOTE: Auth dependency (get_current_user_id) will be implemented by the dev agent.
    """
    # Service layer and auth dependency will be implemented by the dev agent
    from app.services.user_service import update_user_profile
    # current_user_id will come from auth dependency
    current_user_id = 1  # Placeholder - auth dependency will provide this
    return update_user_profile(db, current_user_id, request)


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT,
            summary="Change current user password",
            responses={
                400: {"description": "Invalid current password"},
                401: {"description": "Unauthorized"}
            })
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db)
):
    """
    Change the password of the currently authenticated user.

    Requires current password verification and new password strength validation.
    Requires valid JWT token in Authorization header.

    NOTE: Auth dependency (get_current_user_id) will be implemented by the dev agent.
    """
    # Service layer and auth dependency will be implemented by the dev agent
    from app.services.user_service import change_user_password
    # current_user_id will come from auth dependency
    current_user_id = 1  # Placeholder - auth dependency will provide this
    change_user_password(db, current_user_id, request)