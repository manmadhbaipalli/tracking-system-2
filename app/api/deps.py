"""FastAPI dependencies for database sessions and authentication."""
import logging
from typing import AsyncGenerator

try:
    from circuitbreaker import circuit
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("circuitbreaker package not available. Circuit breaker pattern will be disabled.")
    CIRCUIT_BREAKER_AVAILABLE = False
    # Create a no-op decorator when circuitbreaker is not available
    def circuit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidTokenError
from app.core.security import decode_token
from app.crud.user import get_user_by_email
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer()


if CIRCUIT_BREAKER_AVAILABLE:
    @circuit(
        failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        expected_exception=settings.CIRCUIT_BREAKER_EXPECTED_EXCEPTION,
    )
    async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
        """Get database session with circuit breaker."""
        async for session in get_db():
            yield session
else:
    async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
        """Get database session (circuit breaker disabled - package not available)."""
        async for session in get_db():
            yield session


async def get_current_user(
    db: AsyncSession = Depends(get_database_session),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user