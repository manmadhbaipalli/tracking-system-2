"""Authentication endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest, MessageResponse
from app.core.security import (
    authenticate_user,
    create_access_token,
    hash_password,
)
from app.core.exceptions import AuthenticationException, ConflictException
from app.core.logging import get_logger
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger("app.api.auth")


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Success message

    Raises:
        ConflictException: If email or username already exists
    """
    logger.info(f"User registration attempt for username: {user_data.username}")

    # Check if user with email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        logger.warning(f"Registration failed - email already exists: {user_data.email}")
        raise ConflictException("Email address already registered")

    # Check if user with username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        logger.warning(f"Registration failed - username already exists: {user_data.username}")
        raise ConflictException("Username already taken")

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        is_active=True
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"User registered successfully - ID: {new_user.id}, username: {new_user.username}")
        return MessageResponse(message="User registered successfully")

    except Exception as e:
        await db.rollback()
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT token.

    Args:
        credentials: Login credentials (username/email and password)
        db: Database session

    Returns:
        JWT token response

    Raises:
        AuthenticationException: If credentials are invalid
    """
    logger.info(f"Login attempt for username: {credentials.username}")

    # Authenticate user
    user = await authenticate_user(credentials.username, credentials.password, db)
    if not user:
        logger.warning(f"Login failed for username: {credentials.username}")
        raise AuthenticationException("Invalid username or password")

    if not user.is_active:
        logger.warning(f"Login failed - inactive user: {credentials.username}")
        raise AuthenticationException("Account is deactivated")

    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    logger.info(f"Login successful for user ID: {user.id}, username: {user.username}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60  # Convert to seconds
    )