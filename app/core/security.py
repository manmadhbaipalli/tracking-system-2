"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False  # Allow truncation instead of raising error
)

# OAuth2 scheme for token authentication
security = HTTPBearer()


async def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    # Bcrypt has a 72 byte password limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    # Apply same truncation as when hashing
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


async def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Token payload data
        expires_delta: Token expiration time (optional)

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


async def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData: Decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    return token_data


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        Optional[User]: User object if found, None otherwise
    """
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Union[User, bool]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User's email address
        password: Plain text password

    Returns:
        Union[User, bool]: User object if authentication succeeds, False otherwise
    """
    user = await get_user_by_email(db, email)
    if not user:
        return False
    if not await verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = await verify_token(credentials.credentials)
    user = await get_user_by_email(db, email=token_data.username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current user from authentication

    Returns:
        User: Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user