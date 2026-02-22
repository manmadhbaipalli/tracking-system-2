"""Authentication endpoints for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_database, get_current_user
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import AuthService
from app.core.exceptions import ValidationError, ConflictError, AuthenticationError
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password",
)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_database),
) -> UserResponse:
    """Register a new user account.

    Args:
        user_data: User registration data (email and password)
        db: Database session

    Returns:
        User information without sensitive data

    Raises:
        HTTPException: 400 if validation fails, 409 if email already exists
    """
    try:
        logger.info(f"User registration attempt for email: {user_data.email}")

        # Register user through auth service
        user = await AuthService.register_user(db, user_data)

        logger.info(f"User registered successfully: {user.email}")
        return UserResponse.from_orm(user)

    except ValidationError as e:
        logger.warning(f"Registration validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConflictError as e:
        logger.warning(f"Registration conflict error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and return JWT access token",
)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_database),
) -> Token:
    """Authenticate user and return access token.

    Args:
        login_data: User login credentials (email and password)
        db: Database session

    Returns:
        JWT token information

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    try:
        logger.info(f"Login attempt for email: {login_data.email}")

        # Authenticate user through auth service
        token_data = await AuthService.login_user(db, login_data)

        logger.info(f"User logged in successfully: {login_data.email}")
        return Token(**token_data)

    except AuthenticationError as e:
        logger.warning(f"Authentication failed for {login_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get profile information for the currently authenticated user",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user's profile information.

    Args:
        current_user: Currently authenticated user from JWT token

    Returns:
        Current user's profile information
    """
    logger.info(f"Profile request for user: {current_user.email}")
    return UserResponse.from_orm(current_user)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Generate a new access token for the current user",
)
async def refresh_token(
    current_user: User = Depends(get_current_user),
) -> Token:
    """Refresh the current user's access token.

    Args:
        current_user: Currently authenticated user from JWT token

    Returns:
        New JWT token information
    """
    try:
        logger.info(f"Token refresh request for user: {current_user.email}")

        # Generate new token for current user
        token_data = AuthService.create_user_token(current_user)

        logger.info(f"Token refreshed successfully for user: {current_user.email}")
        return Token(**token_data)

    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User logout",
    description="Logout user (client should discard token)",
)
async def logout_user(
    current_user: User = Depends(get_current_user),
) -> None:
    """Logout current user.

    Note: Since we're using JWT tokens, logout is handled client-side by
    discarding the token. This endpoint is provided for consistency and
    to allow server-side logging of logout events.

    Args:
        current_user: Currently authenticated user from JWT token
    """
    logger.info(f"User logged out: {current_user.email}")
    # With JWT tokens, logout is handled client-side by discarding the token
    # This endpoint is mainly for logging purposes
    return None