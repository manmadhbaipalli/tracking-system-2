import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.security import hash_password, verify_password, create_access_token
from app.exceptions import ConflictException, AuthException

logger = logging.getLogger(__name__)


async def register_user(session: AsyncSession, data: UserRegister) -> User:
    """Register a new user"""
    # Check if email already exists
    result = await session.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictException(f"Email {data.email} is already registered")

    # Create new user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        role=data.role
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("User registered: user_id=%d, email=%s", user.id, user.email)
    return user


async def login_user(session: AsyncSession, data: UserLogin) -> tuple[User, str]:
    """Login user and return user with JWT token"""
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise AuthException("Invalid email or password")

    # Create JWT token
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    logger.info("User logged in: user_id=%d, email=%s", user.id, user.email)
    return user, token


async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
    """Get user by ID"""
    from app.exceptions import NotFoundException
    user = await session.get(User, user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")
    return user
