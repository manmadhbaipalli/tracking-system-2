from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_
from app.models.user import User, UserRole
from typing import Optional, List


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        role: UserRole = UserRole.USER,
        active: bool = True
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            active=active
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user(
        self,
        user_id: int,
        **updates
    ) -> Optional[User]:
        """Update user by ID."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**updates)
        )
        await self.session.commit()
        return await self.get_by_id(user_id)

    async def list_users(
        self,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = False
    ) -> List[User]:
        """List users with pagination and optional active filtering."""
        query = select(User)

        if active_only:
            query = query.where(User.active == True)

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email already exists (for uniqueness validation)."""
        query = select(User).where(User.email == email)

        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def count_users(self, active_only: bool = False) -> int:
        """Count total users for pagination."""
        from sqlalchemy import func

        query = select(func.count(User.id))

        if active_only:
            query = query.where(User.active == True)

        result = await self.session.execute(query)
        return result.scalar()