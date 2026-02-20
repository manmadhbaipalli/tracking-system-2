"""Unit tests for user service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService
from app.models.user import User
from app.utils.password import hash_password
from app.utils.exceptions import UserAlreadyExistsException


@pytest.mark.asyncio
class TestUserService:
    """Test user service operations."""

    async def test_create_user(self, test_db_session: AsyncSession):
        """Test creating a user."""
        service = UserService(test_db_session)
        user = await service.create_user(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True

    async def test_get_user_by_id(self, test_db_session: AsyncSession):
        """Test getting user by ID."""
        service = UserService(test_db_session)
        user = await service.create_user(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        fetched = await service.get_user_by_id(user.id)
        assert fetched.id == user.id
        assert fetched.username == "testuser"

    async def test_get_user_by_id_not_found(self, test_db_session: AsyncSession):
        """Test getting non-existent user returns None."""
        service = UserService(test_db_session)
        user = await service.get_user_by_id(99999)
        assert user is None

    async def test_get_user_by_email(self, test_db_session: AsyncSession):
        """Test getting user by email."""
        service = UserService(test_db_session)
        user = await service.create_user(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        fetched = await service.get_user_by_email("test@example.com")
        assert fetched.id == user.id
        assert fetched.email == "test@example.com"

    async def test_get_user_by_email_case_insensitive(
        self, test_db_session: AsyncSession
    ):
        """Test email lookup is case-insensitive."""
        service = UserService(test_db_session)
        user = await service.create_user(
            username="testuser",
            email="Test@Example.Com",
            hashed_password=hash_password("password123"),
        )
        fetched = await service.get_user_by_email("test@example.com")
        assert fetched is not None
        assert fetched.id == user.id

    async def test_get_user_by_email_not_found(self, test_db_session: AsyncSession):
        """Test getting non-existent user by email returns None."""
        service = UserService(test_db_session)
        user = await service.get_user_by_email("nonexistent@example.com")
        assert user is None

    async def test_get_user_by_username(self, test_db_session: AsyncSession):
        """Test getting user by username."""
        service = UserService(test_db_session)
        user = await service.create_user(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        fetched = await service.get_user_by_username("testuser")
        assert fetched.id == user.id
        assert fetched.username == "testuser"

    async def test_get_user_by_username_not_found(
        self, test_db_session: AsyncSession
    ):
        """Test getting non-existent user by username returns None."""
        service = UserService(test_db_session)
        user = await service.get_user_by_username("nonexistent")
        assert user is None

    async def test_create_duplicate_email_raises_exception(
        self, test_db_session: AsyncSession
    ):
        """Test creating user with duplicate email raises exception."""
        service = UserService(test_db_session)
        await service.create_user(
            username="user1",
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.create_user(
                username="user2",
                email="test@example.com",
                hashed_password=hash_password("password123"),
            )

    async def test_create_duplicate_username_raises_exception(
        self, test_db_session: AsyncSession
    ):
        """Test creating user with duplicate username raises exception."""
        service = UserService(test_db_session)
        await service.create_user(
            username="testuser",
            email="test1@example.com",
            hashed_password=hash_password("password123"),
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.create_user(
                username="testuser",
                email="test2@example.com",
                hashed_password=hash_password("password123"),
            )

    async def test_user_has_timestamps(self, test_db_session: AsyncSession):
        """Test that user has created_at and updated_at timestamps."""
        service = UserService(test_db_session)
        user = await service.create_user(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        assert user.created_at is not None
        assert user.updated_at is not None
