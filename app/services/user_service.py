from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.schemas.common import PageResponse
from app.exceptions import NotFoundException


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = UserRepository(db)

    async def get_by_id(self, user_id: int) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException(f"User {user_id} not found", "USER_NOT_FOUND")
        return UserResponse.model_validate(user)

    async def list_users(self, page: int = 1, page_size: int = 20) -> PageResponse[UserResponse]:
        users, total = await self._repo.list_paginated(page=page, page_size=page_size)
        items = [UserResponse.model_validate(u) for u in users]
        return PageResponse.create(items=items, total=total, page=page, page_size=page_size)
