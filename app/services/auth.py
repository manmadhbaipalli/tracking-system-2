"""Authentication service for user registration and login."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token, is_password_strong
from app.core.exceptions import ValidationError, ConflictError, AuthenticationError
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    async def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created user instance

        Raises:
            ValidationError: If password is not strong enough
            ConflictError: If email is already registered
        """
        # Validate password strength
        if not is_password_strong(user_data.password):
            logger.warning(f"Weak password provided for registration: {user_data.email}")
            raise ValidationError("Password must be at least 8 characters long")

        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            raise ConflictError("Email already registered")

        try:
            # Hash password and create user
            hashed_password = get_password_hash(user_data.password)
            user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                is_active=True,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            logger.info(f"User registered successfully: {user.email}")
            return user

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error during user registration: {str(e)}")
            raise ConflictError("Email already registered")
        except Exception as e:
            db.rollback()
            logger.error(f"Error registering user: {str(e)}")
            raise ValidationError("Registration failed")

    @staticmethod
    async def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password.

        Args:
            db: Database session
            email: User email
            password: User password

        Returns:
            User instance if authentication successful, None otherwise
        """
        try:
            # Get user by email
            user = db.query(User).filter(User.email == email).first()
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                return None

            # Verify password
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Invalid password for user: {email}")
                return None

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt by inactive user: {email}")
                return None

            logger.info(f"User authenticated successfully: {email}")
            return user

        except Exception as e:
            logger.error(f"Error during user authentication: {str(e)}")
            return None

    @staticmethod
    def create_user_token(user: User) -> dict:
        """Create JWT token for authenticated user.

        Args:
            user: Authenticated user

        Returns:
            Dictionary with token information
        """
        access_token = create_access_token(subject=str(user.id))

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        }

    @staticmethod
    async def login_user(db: Session, login_data: UserLogin) -> dict:
        """Login user and return token.

        Args:
            db: Database session
            login_data: User login credentials

        Returns:
            Dictionary with token information

        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = await AuthService.authenticate_user(
            db, login_data.email, login_data.password
        )
        if not user:
            raise AuthenticationError("Invalid email or password")

        return AuthService.create_user_token(user)

    @staticmethod
    async def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User instance if found, None otherwise
        """
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            return None

    @staticmethod
    async def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User instance if found, None otherwise
        """
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            return None