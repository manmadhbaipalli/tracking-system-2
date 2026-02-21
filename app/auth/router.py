"""FastAPI router for authentication endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.auth.service import (
    register_user,
    login_user,
    create_access_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_endpoint(
    user_data: UserRegister,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user response
    """
    user = register_user(user_data.email, user_data.password, db)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login_endpoint(
    user_data: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Login a user.

    Args:
        user_data: User login data
        db: Database session

    Returns:
        Token response with JWT access token
    """
    user = login_user(user_data.email, user_data.password, db)
    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token, token_type="bearer")
