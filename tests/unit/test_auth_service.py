"""Unit tests for authentication service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.utils.password import hash_password, verify_password
from app.utils.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    ValidationException,
)


@pytest.mark.asyncio
class TestAuthService:
    """Test authentication service operations."""

    async def test_register_user_success(self, test_db_session: AsyncSession):
        """Test successful user registration."""
        service = AuthService(test_db_session)
        response = await service.register_user(
            email="newuser@example.com",
            username="newuser",
            password="securepass123",
        )
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.token_type == "bearer"
        assert response.user.username == "newuser"
        assert response.user.email == "newuser@example.com"

    async def test_register_user_with_short_password(
        self, test_db_session: AsyncSession
    ):
        """Test registration fails with short password."""
        service = AuthService(test_db_session)
        with pytest.raises(ValidationException):
            await service.register_user(
                email="newuser@example.com",
                username="newuser",
                password="short",
            )

    async def test_register_user_missing_email(self, test_db_session: AsyncSession):
        """Test registration fails with missing email."""
        service = AuthService(test_db_session)
        with pytest.raises(ValidationException):
            await service.register_user(
                email="",
                username="newuser",
                password="securepass123",
            )

    async def test_register_user_missing_username(self, test_db_session: AsyncSession):
        """Test registration fails with missing username."""
        service = AuthService(test_db_session)
        with pytest.raises(ValidationException):
            await service.register_user(
                email="newuser@example.com",
                username="",
                password="securepass123",
            )

    async def test_register_user_missing_password(self, test_db_session: AsyncSession):
        """Test registration fails with missing password."""
        service = AuthService(test_db_session)
        with pytest.raises(ValidationException):
            await service.register_user(
                email="newuser@example.com",
                username="newuser",
                password="",
            )

    async def test_register_user_duplicate_email(self, test_db_session: AsyncSession):
        """Test registration fails with duplicate email."""
        service = AuthService(test_db_session)
        await service.register_user(
            email="existing@example.com",
            username="user1",
            password="securepass123",
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.register_user(
                email="existing@example.com",
                username="user2",
                password="securepass123",
            )

    async def test_register_user_duplicate_username(self, test_db_session: AsyncSession):
        """Test registration fails with duplicate username."""
        service = AuthService(test_db_session)
        await service.register_user(
            email="user1@example.com",
            username="duplicate",
            password="securepass123",
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.register_user(
                email="user2@example.com",
                username="duplicate",
                password="securepass123",
            )

    async def test_login_with_email_success(self, test_db_session: AsyncSession):
        """Test successful login with email."""
        service = AuthService(test_db_session)
        # Register user
        await service.register_user(
            email="testuser@example.com",
            username="testuser",
            password="securepass123",
        )
        # Login
        response = await service.login(
            email="testuser@example.com",
            password="securepass123",
        )
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.user.email == "testuser@example.com"

    async def test_login_with_username_success(self, test_db_session: AsyncSession):
        """Test successful login with username."""
        service = AuthService(test_db_session)
        await service.register_user(
            email="testuser@example.com",
            username="testuser",
            password="securepass123",
        )
        response = await service.login(
            username="testuser",
            password="securepass123",
        )
        assert response.access_token is not None
        assert response.user.username == "testuser"

    async def test_login_wrong_password(self, test_db_session: AsyncSession):
        """Test login fails with wrong password."""
        service = AuthService(test_db_session)
        await service.register_user(
            email="testuser@example.com",
            username="testuser",
            password="securepass123",
        )
        with pytest.raises(InvalidCredentialsException):
            await service.login(
                email="testuser@example.com",
                password="wrongpassword",
            )

    async def test_login_nonexistent_user(self, test_db_session: AsyncSession):
        """Test login fails for non-existent user."""
        service = AuthService(test_db_session)
        with pytest.raises(InvalidCredentialsException):
            await service.login(
                email="nonexistent@example.com",
                password="anypassword",
            )

    async def test_login_missing_credentials(self, test_db_session: AsyncSession):
        """Test login fails with missing credentials."""
        service = AuthService(test_db_session)
        with pytest.raises(InvalidCredentialsException):
            await service.login(password="securepass123")

    async def test_login_missing_password(self, test_db_session: AsyncSession):
        """Test login fails with missing password."""
        service = AuthService(test_db_session)
        with pytest.raises(InvalidCredentialsException):
            await service.login(email="testuser@example.com")

    async def test_refresh_access_token_success(self, test_db_session: AsyncSession):
        """Test successful token refresh."""
        service = AuthService(test_db_session)
        register_response = await service.register_user(
            email="testuser@example.com",
            username="testuser",
            password="securepass123",
        )
        refresh_response = await service.refresh_access_token(
            register_response.refresh_token
        )
        assert refresh_response.access_token is not None
        assert refresh_response.refresh_token == register_response.refresh_token
        assert refresh_response.user.id == register_response.user.id

    async def test_refresh_invalid_token(self, test_db_session: AsyncSession):
        """Test token refresh fails with invalid token."""
        service = AuthService(test_db_session)
        with pytest.raises(InvalidCredentialsException):
            await service.refresh_access_token("invalid.token.here")

    async def test_refresh_token_for_deleted_user(
        self, test_db_session: AsyncSession
    ):
        """Test token refresh fails if user no longer exists."""
        from app.services.user_service import UserService
        from app.utils.jwt import create_refresh_token

        service = AuthService(test_db_session)
        user_service = UserService(test_db_session)

        # Create and delete user
        user = await user_service.create_user(
            username="tempuser",
            email="temp@example.com",
            hashed_password=hash_password("password123"),
        )
        refresh_token = create_refresh_token(user.id)

        # Delete user (in real scenario)
        # For this test, we just create a token for non-existent user
        fake_token = create_refresh_token(99999)

        with pytest.raises(InvalidCredentialsException):
            await service.refresh_access_token(fake_token)

    async def test_password_hashed_in_database(self, test_db_session: AsyncSession):
        """Test that passwords are hashed in database."""
        from app.services.user_service import UserService

        service = AuthService(test_db_session)
        user_service = UserService(test_db_session)

        password = "myplainpassword"
        await service.register_user(
            email="test@example.com",
            username="testuser",
            password=password,
        )

        user = await user_service.get_user_by_email("test@example.com")
        assert user.hashed_password != password
        assert verify_password(password, user.hashed_password)

    async def test_email_case_normalization(self, test_db_session: AsyncSession):
        """Test that emails are normalized to lowercase."""
        service = AuthService(test_db_session)
        response = await service.register_user(
            email="TestUser@EXAMPLE.COM",
            username="testuser",
            password="securepass123",
        )
        assert response.user.email == "testuser@example.com"

    async def test_login_with_uppercase_email(self, test_db_session: AsyncSession):
        """Test login with uppercase email works."""
        service = AuthService(test_db_session)
        await service.register_user(
            email="testuser@example.com",
            username="testuser",
            password="securepass123",
        )
        response = await service.login(
            email="TESTUSER@EXAMPLE.COM",
            password="securepass123",
        )
        assert response.user.email == "testuser@example.com"
