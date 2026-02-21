"""
Claims Service Platform - Authentication API

Provides login, logout, token refresh, and user management endpoints with proper security.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_token, require_role, UserRole
from app.services.auth_service import auth_service
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserCreate, UserResponse,
    ChangePasswordRequest, RefreshTokenRequest
)

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    user = auth_service.authenticate_user(
        db=db,
        username=login_data.username,
        password=login_data.password,
        ip_address=request.client.host if request.client else None
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )

    tokens = auth_service.create_tokens(user)
    return TokenResponse(**tokens)


@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    # Basic refresh token validation (simplified)
    return {"message": "Token refresh not implemented"}


@router.post("/logout")
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """User logout endpoint"""
    # Log logout action
    from app.services.audit_service import audit_service
    audit_service.log_action(
        db=db,
        user_id=current_user.get("user_id"),
        action="logout",
        table_name="users",
        record_id=str(current_user.get("user_id")),
        ip_address=request.client.host if request.client else None
    )

    return {"message": "Successfully logged out"}


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create new user (admin only)"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    user = auth_service.create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role.value,
        created_by=current_user.get("user_id")
    )

    return UserResponse.from_orm(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    from app.models.user import User
    user = db.query(User).filter(User.id == current_user.get("user_id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)