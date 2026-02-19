"""Dependency injection configuration for FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session as _get_db_session
from app.utils.jwt import extract_user_id_from_token
from app.utils.exceptions import TokenExpiredException
from app.utils.logger import get_logger, get_request_id as get_request_id_util
from app.services.user_service import UserService
from app.models.user import User

logger = get_logger(__name__)

security = HTTPBearer()


async def get_db_session() -> AsyncSession:
    """Provide database session."""
    async for session in _get_db_session():
        yield session


async def get_current_user(
    credentials=Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Get current authenticated user from JWT token."""
    try:
        token = credentials.credentials
        user_id = extract_user_id_from_token(token)
    except TokenExpiredException:
        logger.warning("Invalid token in authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user_service = UserService(session)
    user = await user_service.get_user_by_id(user_id)

    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return user


async def get_request_id() -> str:
    """Get current request ID."""
    return get_request_id_util()
