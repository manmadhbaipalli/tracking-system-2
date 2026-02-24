"""
Authentication service with JWT token management and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from uuid import UUID

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserCreate
from app.utils.exceptions import AuthenticationError, ValidationError


class AuthService:
    """Service layer for authentication and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        try:
            # Get user by email
            stmt = select(User).where(User.email == email, User.is_active == True)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            if not self.verify_password(password, user.hashed_password):
                return None

            return user
        except Exception as e:
            raise AuthenticationError("Authentication failed")

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None

    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token."""
        payload = self.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            stmt = select(User).where(User.id == UUID(user_id), User.is_active == True)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def login(self, login_data: LoginRequest) -> LoginResponse:
        """Authenticate user and return tokens."""
        user = await self.authenticate_user(login_data.email, login_data.password)

        if not user:
            raise AuthenticationError("Invalid email or password")

        # Create tokens
        access_token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        access_token = self.create_access_token(access_token_data)
        refresh_token = self.create_refresh_token({"sub": str(user.id)})

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            role=user.role
        )

    async def register(self, register_data: UserCreate, user_id: UUID) -> User:
        """Register a new user."""
        # Check if user already exists
        stmt = select(User).where(User.email == register_data.email)
        result = await self.db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValidationError("Email already registered")

        # Create new user
        hashed_password = self.get_password_hash(register_data.password)

        user = User(
            email=register_data.email,
            hashed_password=hashed_password,
            first_name=register_data.first_name,
            last_name=register_data.last_name,
            role=register_data.role,
            is_active=True,
            created_by=user_id,
            updated_by=user_id
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def refresh_access_token(self, refresh_token: str) -> LoginResponse:
        """Refresh access token using refresh token."""
        payload = self.verify_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token")

        # Get user
        user = await self.get_current_user_by_id(UUID(user_id))
        if not user:
            raise AuthenticationError("User not found")

        # Create new tokens
        access_token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        access_token = self.create_access_token(access_token_data)
        new_refresh_token = self.create_refresh_token({"sub": str(user.id)})

        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            role=user.role
        )

    async def get_current_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        try:
            stmt = select(User).where(User.id == user_id, User.is_active == True)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            return None