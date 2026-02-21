"""Authentication API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import logging

from ..database import get_db
from ..models.user import User
from ..schemas.auth import UserRegister, UserLogin, Token, RefreshTokenRequest
from ..schemas.user import UserResponse
from ..core.auth import (
    create_access_token,
    create_refresh_token,
    authenticate_user,
    verify_token
)
from ..core.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
    DatabaseError,
    ValidationError
)
from ..utils.password import hash_password

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        UserResponse: Created user data

    Raises:
        UserAlreadyExistsError: If user with email already exists
        DatabaseError: If database operation fails
    """
    logger.info(f"User registration attempt for email: {user_data.email}")

    try:
        # Check if user already exists
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Registration failed - user already exists: {user_data.email}")
            raise UserAlreadyExistsError(
                message="User with this email already exists",
                details={"email": user_data.email}
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create new user
        new_user = User(
            email=user_data.email,
            password_hash=password_hash,
            is_active=True
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"User registered successfully: {new_user.id}")
        return UserResponse.model_validate(new_user)

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        raise UserAlreadyExistsError(
            message="User with this email already exists",
            details={"email": user_data.email}
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during registration: {e}")
        raise DatabaseError(
            message="Failed to create user account",
            details={"error": str(e)}
        )


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and return JWT tokens"
)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Authenticate user and return JWT tokens.

    Args:
        user_credentials: User login credentials
        db: Database session

    Returns:
        Token: JWT access and refresh tokens

    Raises:
        AuthenticationError: If authentication fails
    """
    logger.info(f"Login attempt for email: {user_credentials.email}")

    # Authenticate user
    user = await authenticate_user(
        db=db,
        email=user_credentials.email,
        password=user_credentials.password
    )

    if not user:
        logger.warning(f"Authentication failed for email: {user_credentials.email}")
        raise AuthenticationError(
            message="Invalid email or password",
            details={"email": user_credentials.email}
        )

    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {user_credentials.email}")
        raise AuthenticationError(
            message="User account is inactive",
            details={"email": user_credentials.email}
        )

    # Create tokens
    token_data = {"sub": user.email, "user_id": user.id}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    logger.info(f"User logged in successfully: {user.id}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post(
    "/refresh-token",
    response_model=Token,
    summary="Refresh access token",
    description="Exchange refresh token for new access token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token request
        db: Database session

    Returns:
        Token: New JWT access and refresh tokens

    Raises:
        AuthenticationError: If refresh token is invalid
    """
    logger.info("Token refresh attempt")

    try:
        # Verify refresh token
        token_data = verify_token(refresh_data.refresh_token, token_type="refresh")

        # Get user from database
        stmt = select(User).where(User.email == token_data.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            logger.warning(f"Token refresh failed - user not found or inactive: {token_data.email}")
            raise AuthenticationError(
                message="Invalid refresh token or user account inactive"
            )

        # Create new tokens
        new_token_data = {"sub": user.email, "user_id": user.id}
        new_access_token = create_access_token(data=new_token_data)
        new_refresh_token = create_refresh_token(data=new_token_data)

        logger.info(f"Token refreshed successfully for user: {user.id}")

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        # Re-raise HTTP exceptions from token verification
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise AuthenticationError(
            message="Failed to refresh token",
            details={"error": str(e)}
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout user (token invalidation would require token blacklisting)"
)
async def logout() -> dict:
    """
    Logout user.

    Note: In a JWT-based system without token blacklisting,
    logout is primarily client-side (removing tokens from storage).

    Returns:
        dict: Success message
    """
    logger.info("User logout")

    return {
        "message": "Successfully logged out",
        "detail": "Please remove tokens from client storage"
    }