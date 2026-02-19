"""Authentication business logic including registration, login, and token refresh."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import TokenResponse, UserResponse
from app.services.user_service import UserService
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.jwt import extract_user_id_from_token
from app.utils.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    TokenExpiredException,
    ValidationException,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self.user_service = UserService(session)

    async def register_user(
        self, email: str, username: str, password: str
    ) -> TokenResponse:
        """Register a new user."""
        # Validate input
        if not email or not username or not password:
            raise ValidationException("Missing required fields")

        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters")

        # Check if user already exists
        existing_by_email = await self.user_service.get_user_by_email(email)
        if existing_by_email:
            logger.warning(f"Registration failed - email exists: {email}")
            raise UserAlreadyExistsException("email")

        existing_by_username = await self.user_service.get_user_by_username(
            username
        )
        if existing_by_username:
            logger.warning(f"Registration failed - username exists: {username}")
            raise UserAlreadyExistsException("username")

        # Hash password and create user
        hashed_password = hash_password(password)
        user = await self.user_service.create_user(
            username, email, hashed_password
        )

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        logger.info(f"User registered: {user.id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def login(
        self,
        email: str = None,
        username: str = None,
        password: str = None,
    ) -> TokenResponse:
        """Authenticate user and return tokens."""
        if not password:
            raise InvalidCredentialsException()

        if not email and not username:
            raise InvalidCredentialsException()

        # Find user by email or username
        user = None
        if email:
            user = await self.user_service.get_user_by_email(email)
        elif username:
            user = await self.user_service.get_user_by_username(username)

        # Verify credentials (generic error message)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Login failed - invalid credentials")
            raise InvalidCredentialsException()

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed - user inactive: {user.id}")
            raise InvalidCredentialsException()

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        logger.info(f"User login successful: {user.id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def refresh_access_token(
        self, refresh_token: str
    ) -> TokenResponse:
        """Generate new access token using refresh token."""
        try:
            user_id = extract_user_id_from_token(refresh_token)
        except TokenExpiredException:
            logger.warning("Refresh token validation failed")
            raise InvalidCredentialsException()

        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Refresh failed - user not found: {user_id}")
            raise InvalidCredentialsException()

        # Generate new access token
        access_token = create_access_token(user.id)

        logger.info(f"Access token refreshed: {user.id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
