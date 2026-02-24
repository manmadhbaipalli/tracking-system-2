from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.security import get_current_user_id
from app.schemas.user import UserResponse, UpdateProfileRequest, ChangePasswordRequest
from app.services.user_service import get_user_profile, update_user_profile, change_password

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the authenticated user's profile.",
)
async def get_me(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_profile(db, current_user_id)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the authenticated user's profile information.",
)
async def update_me(
    request: UpdateProfileRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await update_user_profile(db, current_user_id, full_name=request.full_name)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change the authenticated user's password.",
)
async def change_my_password(
    request: ChangePasswordRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await change_password(db, current_user_id, request.current_password, request.new_password)
