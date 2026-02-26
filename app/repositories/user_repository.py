from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.enums import Role


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Case-insensitive lookup by email."""
        result = await self._session.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password_hash: str,
        name: str,
        role: Role = Role.USER,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
            active=True,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def list_paginated(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        """Return (items, total) for pagination."""
        offset = (page - 1) * page_size

        total_result = await self._session.execute(
            select(func.count()).select_from(User)
        )
        total = total_result.scalar_one()

        items_result = await self._session.execute(
            select(User).order_by(User.id).offset(offset).limit(page_size)
        )
        items = list(items_result.scalars().all())

        return items, total
