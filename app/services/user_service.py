"""User management business logic service."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.exceptions import UserAlreadyExistsException
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self, username: str, email: str, hashed_password: str
    ) -> User:
        """Create a new user."""
        user = User(
            username=username,
            email=email.lower(),
            hashed_password=hashed_password,
            is_active=True,
        )

        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"User created: {user.id}")
            return user
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"User creation failed - duplicate: {email}")
            if "username" in str(e):
                raise UserAlreadyExistsException("username")
            elif "email" in str(e):
                raise UserAlreadyExistsException("email")
            raise UserAlreadyExistsException()
