"""
Authentication endpoints for login, token refresh, user registration, and role management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    UserCreate,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    LoginRequest
)
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a new user."""
    auth_service = AuthService(db)

    # Convert UserCreate to RegisterRequest schema format
    from app.schemas.auth import UserCreate as RegisterRequest

    user = await auth_service.register(user_data, current_user.id)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login user and return JWT token."""
    auth_service = AuthService(db)

    # Convert OAuth2PasswordRequestForm to LoginRequest
    login_request = LoginRequest(email=form_data.username, password=form_data.password)

    login_response = await auth_service.login(login_request)

    return TokenResponse(
        access_token=login_response.access_token,
        refresh_token=login_response.refresh_token,
        token_type=login_response.token_type,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserResponse(
            id=login_response.user_id,
            email=login_response.email,
            first_name="",  # Will be populated from user lookup
            last_name="",   # Will be populated from user lookup
            role=login_response.role,
            is_active=True,
            last_login=None,
            created_at=None
        )
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh JWT token."""
    auth_service = AuthService(db)

    login_response = await auth_service.refresh_access_token(refresh_data.refresh_token)

    return TokenResponse(
        access_token=login_response.access_token,
        refresh_token=login_response.refresh_token,
        token_type=login_response.token_type,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserResponse(
            id=login_response.user_id,
            email=login_response.email,
            first_name="",  # Will be populated from user lookup
            last_name="",   # Will be populated from user lookup
            role=login_response.role,
            is_active=True,
            last_login=None,
            created_at=None
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)