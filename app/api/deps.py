"""Dependency injection for FastAPI endpoints."""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Security scheme for JWT authentication
security = HTTPBearer()


def get_database() -> Generator[Session, None, None]:
    """Get database session dependency.

    Yields:
        Database session
    """
    yield from get_db()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database),
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials containing JWT token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        AuthenticationError: If token is invalid or user not found
    """
    try:
        # Verify the token and extract user ID
        user_id = verify_token(credentials.credentials)
        if user_id is None:
            logger.warning("Invalid token provided")
            raise AuthenticationError("Invalid authentication token")

        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            logger.warning(f"User not found for ID: {user_id}")
            raise AuthenticationError("User not found")

        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user.email}")
            raise AuthenticationError("Inactive user account")

        logger.info(f"User authenticated successfully: {user.email}")
        return user

    except ValueError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise AuthenticationError("Invalid authentication token")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise AuthenticationError("Authentication failed")


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (additional check for active status).

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        AuthenticationError: If user is not active
    """
    if not current_user.is_active:
        raise AuthenticationError("Inactive user account")
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_database),
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None.

    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session

    Returns:
        Current user if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        user_id = verify_token(credentials.credentials)
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None or not user.is_active:
            return None

        return user
    except Exception:
        return None