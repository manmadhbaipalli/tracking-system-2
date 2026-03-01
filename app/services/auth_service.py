import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from app.security import hash_password, verify_password, create_access_token
from app.exceptions import NotFoundException, ConflictException, AuthException

logger = logging.getLogger(__name__)


async def register_user(session: AsyncSession, data: RegisterRequest) -> UserResponse:
    """Register a new user with email, password, and name"""
    logger.info("Attempting to register user with email: %s", data.email)

    # Check if email already exists
    result = await session.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning("Registration failed: email already exists: %s", data.email)
        raise ConflictException(f"Email {data.email} is already registered")

    # Create new user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        is_active=True
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info("User registered successfully: user_id=%d, email=%s", user.id, user.email)
    return UserResponse.model_validate(user)


async def login_user(session: AsyncSession, data: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT access token"""
    logger.info("Login attempt for email: %s", data.email)

    # Find user by email
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Login failed: user not found for email: %s", data.email)
        raise AuthException("Invalid email or password")

    # Verify password
    if not verify_password(data.password, user.password_hash):
        logger.warning("Login failed: invalid password for email: %s", data.email)
        raise AuthException("Invalid email or password")

    # Check if user is active
    if not user.is_active:
        logger.warning("Login failed: user is inactive: user_id=%d", user.id)
        raise AuthException("User account is inactive")

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    logger.info("Login successful: user_id=%d, email=%s", user.id, user.email)
    return TokenResponse(access_token=access_token, token_type="bearer")


async def get_current_user(session: AsyncSession, user_id: int) -> UserResponse:
    """Get current authenticated user profile"""
    logger.info("Fetching user profile: user_id=%d", user_id)

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("User not found: user_id=%d", user_id)
        raise NotFoundException(f"User with id {user_id} not found")

    return UserResponse.model_validate(user)
