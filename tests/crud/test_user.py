"""Tests for user CRUD operations."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserExistsError
from app.crud.user import authenticate_user, create_user, get_user_by_email, get_user_by_id
from app.schemas.user import UserCreate


class TestUserCRUD:
    """Test cases for user CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_db_session: AsyncSession):
        """Test successful user creation."""
        user_data = UserCreate(email="test@example.com", password="testpassword123")
        user = await create_user(test_db_session, user_data)

        assert user.email == "test@example.com"
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.hashed_password != "testpassword123"  # Should be hashed
        assert len(user.hashed_password) > 10  # Hashed password should be longer
        assert user.is_active is True
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, test_db_session: AsyncSession):
        """Test creating user with duplicate email fails."""
        user_data = UserCreate(email="test@example.com", password="testpassword123")

        # Create first user
        user1 = await create_user(test_db_session, user_data)
        assert user1 is not None

        # Attempt to create duplicate user
        with pytest.raises(UserExistsError) as exc_info:
            await create_user(test_db_session, user_data)

        assert "already exists" in str(exc_info.value)
        assert "test@example.com" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_by_email_exists(self, test_db_session: AsyncSession):
        """Test getting user by email when user exists."""
        user_data = UserCreate(email="test@example.com", password="testpassword123")
        created_user = await create_user(test_db_session, user_data)

        retrieved_user = await get_user_by_email(test_db_session, "test@example.com")
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_exists(self, test_db_session: AsyncSession):
        """Test getting user by email when user doesn't exist."""
        user = await get_user_by_email(test_db_session, "nonexistent@example.com")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_exists(self, test_db_session: AsyncSession):
        """Test getting user by ID when user exists."""
        user_data = UserCreate(email="test@example.com", password="testpassword123")
        created_user = await create_user(test_db_session, user_data)

        retrieved_user = await get_user_by_id(test_db_session, str(created_user.id))
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_exists(self, test_db_session: AsyncSession):
        """Test getting user by ID when user doesn't exist."""
        fake_uuid = str(uuid.uuid4())
        user = await get_user_by_id(test_db_session, fake_uuid)
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, test_db_session: AsyncSession):
        """Test successful user authentication."""
        user_data = UserCreate(email="test@example.com", password="testpassword123")
        created_user = await create_user(test_db_session, user_data)

        authenticated_user = await authenticate_user(
            test_db_session, "test@example.com", "testpassword123"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.email == created_user.email

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, test_db_session: AsyncSession):
        """Test authentication with wrong password."""
        user_data = UserCreate(email="test@example.com", password="testpassword123")
        await create_user(test_db_session, user_data)

        authenticated_user = await authenticate_user(
            test_db_session, "test@example.com", "wrongpassword"
        )
        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_email(self, test_db_session: AsyncSession):
        """Test authentication with nonexistent email."""
        authenticated_user = await authenticate_user(
            test_db_session, "nonexistent@example.com", "anypassword"
        )
        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_password_hashing_security(self, test_db_session: AsyncSession):
        """Test that passwords are properly hashed and unique."""
        password = "samepassword123"

        # Create two users with same password
        user_data1 = UserCreate(email="user1@example.com", password=password)
        user_data2 = UserCreate(email="user2@example.com", password=password)

        user1 = await create_user(test_db_session, user_data1)
        user2 = await create_user(test_db_session, user_data2)

        # Hashed passwords should be different due to salt
        assert user1.hashed_password != user2.hashed_password
        # Neither should match the plaintext password
        assert user1.hashed_password != password
        assert user2.hashed_password != password
        # Both should be properly formatted bcrypt hashes
        assert user1.hashed_password.startswith("$2b$")
        assert user2.hashed_password.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_user_email_case_sensitivity(self, test_db_session: AsyncSession):
        """Test that email lookups are case-sensitive as per current implementation."""
        user_data = UserCreate(email="Test@Example.com", password="testpassword123")
        created_user = await create_user(test_db_session, user_data)

        # Exact match should work
        user_exact = await get_user_by_email(test_db_session, "Test@Example.com")
        assert user_exact is not None
        assert user_exact.id == created_user.id

        # Different case should not work (current implementation is case-sensitive)
        user_different_case = await get_user_by_email(test_db_session, "test@example.com")
        assert user_different_case is None