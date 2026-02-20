"""Tests for database models."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.user import User


class TestUserModel:
    """Test User model functionality."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession):
        """Test creating a valid user."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_here",
            is_active=True
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Verify user was created with expected values
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password_here"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_user_default_values(self, db_session: AsyncSession):
        """Test user model default values."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_here"
            # Not setting is_active explicitly
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # is_active should default to True
        assert user.is_active is True
        # created_at and updated_at should be automatically set
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_timestamps(self, db_session: AsyncSession):
        """Test that timestamps are properly managed."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_here",
            is_active=True
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        original_created_at = user.created_at
        original_updated_at = user.updated_at

        # Verify timestamps are set
        assert original_created_at is not None
        assert original_updated_at is not None

        # Update the user
        user.email = "updated@example.com"
        await db_session.commit()
        await db_session.refresh(user)

        # created_at should remain the same, updated_at should change
        assert user.created_at == original_created_at
        assert user.updated_at != original_updated_at
        assert user.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_user_unique_email_constraint(self, db_session: AsyncSession):
        """Test that email uniqueness constraint is enforced."""
        # Create first user
        user1 = User(
            email="test@example.com",
            username="testuser1",
            hashed_password="password1",
            is_active=True
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create second user with same email
        user2 = User(
            email="test@example.com",  # Same email
            username="testuser2",
            hashed_password="password2",
            is_active=True
        )
        db_session.add(user2)

        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_unique_username_constraint(self, db_session: AsyncSession):
        """Test that username uniqueness constraint is enforced."""
        # Create first user
        user1 = User(
            email="test1@example.com",
            username="testuser",
            hashed_password="password1",
            is_active=True
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create second user with same username
        user2 = User(
            email="test2@example.com",
            username="testuser",  # Same username
            hashed_password="password2",
            is_active=True
        )
        db_session.add(user2)

        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_required_fields(self, db_session: AsyncSession):
        """Test that required fields are enforced."""
        # Try to create user without email
        with pytest.raises(Exception):  # Should be a database constraint error
            user = User(
                username="testuser",
                hashed_password="password",
                is_active=True
            )
            db_session.add(user)
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_string_representation(self, db_session: AsyncSession):
        """Test user model string representation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="password",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Test __repr__ method
        repr_str = repr(user)
        assert "User(" in repr_str
        assert str(user.id) in repr_str
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str

    @pytest.mark.asyncio
    async def test_user_field_lengths(self, db_session: AsyncSession):
        """Test field length constraints."""
        # Test email field length (255 chars)
        long_email = "a" * 240 + "@example.com"  # Total 252 chars, within limit
        user = User(
            email=long_email,
            username="testuser",
            hashed_password="password",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.email == long_email

    @pytest.mark.asyncio
    async def test_user_boolean_fields(self, db_session: AsyncSession):
        """Test boolean field handling."""
        # Test active user
        active_user = User(
            email="active@example.com",
            username="activeuser",
            hashed_password="password",
            is_active=True
        )
        db_session.add(active_user)

        # Test inactive user
        inactive_user = User(
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password="password",
            is_active=False
        )
        db_session.add(inactive_user)

        await db_session.commit()

        # Query and verify
        result = await db_session.execute(
            select(User).where(User.is_active == True)
        )
        active_users = result.scalars().all()
        assert len(active_users) == 1
        assert active_users[0].username == "activeuser"

        result = await db_session.execute(
            select(User).where(User.is_active == False)
        )
        inactive_users = result.scalars().all()
        assert len(inactive_users) == 1
        assert inactive_users[0].username == "inactiveuser"


class TestUserModelIndexes:
    """Test User model database indexes."""

    @pytest.mark.asyncio
    async def test_user_email_index(self, db_session: AsyncSession):
        """Test that email index allows efficient queries."""
        # Create multiple users
        users_data = [
            ("user1@example.com", "user1"),
            ("user2@example.com", "user2"),
            ("user3@example.com", "user3"),
        ]

        for email, username in users_data:
            user = User(
                email=email,
                username=username,
                hashed_password="password",
                is_active=True
            )
            db_session.add(user)

        await db_session.commit()

        # Query by email (should use index)
        result = await db_session.execute(
            select(User).where(User.email == "user2@example.com")
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.username == "user2"

    @pytest.mark.asyncio
    async def test_user_username_index(self, db_session: AsyncSession):
        """Test that username index allows efficient queries."""
        # Create multiple users
        users_data = [
            ("user1@example.com", "username1"),
            ("user2@example.com", "username2"),
            ("user3@example.com", "username3"),
        ]

        for email, username in users_data:
            user = User(
                email=email,
                username=username,
                hashed_password="password",
                is_active=True
            )
            db_session.add(user)

        await db_session.commit()

        # Query by username (should use index)
        result = await db_session.execute(
            select(User).where(User.username == "username2")
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.email == "user2@example.com"

    @pytest.mark.asyncio
    async def test_compound_index_usage(self, db_session: AsyncSession):
        """Test compound index usage for performance queries."""
        # Create users with different active states
        users_data = [
            ("active1@example.com", "active1", True),
            ("active2@example.com", "active2", True),
            ("inactive1@example.com", "inactive1", False),
            ("inactive2@example.com", "inactive2", False),
        ]

        for email, username, is_active in users_data:
            user = User(
                email=email,
                username=username,
                hashed_password="password",
                is_active=is_active
            )
            db_session.add(user)

        await db_session.commit()

        # Query using compound index (email + is_active)
        result = await db_session.execute(
            select(User).where(
                User.email == "active1@example.com",
                User.is_active == True
            )
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.username == "active1"

        # Query using compound index (username + is_active)
        result = await db_session.execute(
            select(User).where(
                User.username == "inactive1",
                User.is_active == False
            )
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.email == "inactive1@example.com"