"""Authentication endpoints for user registration and login."""

from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.circuit_breaker import circuit_breaker
from app.core.exceptions import UserAlreadyExistsError, AuthenticationError
from app.core.security import (
    authenticate_user,
    create_access_token,
    hash_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.schemas.user import UserResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@circuit_breaker("user_registration", failure_threshold=5, recovery_timeout=30)
async def create_user_in_db(db: AsyncSession, user_data: UserRegisterRequest) -> User:
    """
    Create a new user in the database with circuit breaker protection.

    Args:
        db: Database session
        user_data: User registration data

    Returns:
        User: Created user object

    Raises:
        UserAlreadyExistsError: If user with email already exists
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise UserAlreadyExistsError("User with this email already exists")

    # Create new user
    hashed_password = await hash_password(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
    )

    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError("User with this email already exists")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        UserResponse: Created user information (excluding password)

    Raises:
        HTTPException: If user already exists or registration fails
    """
    try:
        logger.info("User registration attempt", email=user_data.email)
        user = await create_user_in_db(db, user_data)
        logger.info("User registered successfully", user_id=str(user.id), email=user.email)
        return UserResponse.model_validate(user)

    except UserAlreadyExistsError as e:
        logger.warning("Registration failed - user exists", email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Registration failed", email=user_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@circuit_breaker("user_authentication", failure_threshold=5, recovery_timeout=30)
async def authenticate_user_with_cb(
    db: AsyncSession, email: str, password: str
) -> User:
    """
    Authenticate user with circuit breaker protection.

    Args:
        db: Database session
        email: User email
        password: User password

    Returns:
        User: Authenticated user

    Raises:
        AuthenticationError: If authentication fails
    """
    user = await authenticate_user(db, email, password)
    if not user:
        raise AuthenticationError("Invalid email or password")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return access token.

    Args:
        login_data: User login credentials
        db: Database session

    Returns:
        TokenResponse: JWT access token and metadata

    Raises:
        HTTPException: If authentication fails
    """
    try:
        logger.info("User login attempt", email=login_data.email)
        user = await authenticate_user_with_cb(db, login_data.email, login_data.password)

        if not user.is_active:
            logger.warning("Login failed - inactive user", email=login_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = await create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        logger.info("User logged in successfully", user_id=str(user.id), email=user.email)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    except AuthenticationError as e:
        logger.warning("Login failed - invalid credentials", email=login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Login failed", email=login_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token() -> TokenResponse:
    """
    Refresh an access token (future enhancement).

    Returns:
        TokenResponse: New JWT access token

    Raises:
        HTTPException: Not implemented
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented yet"
    )