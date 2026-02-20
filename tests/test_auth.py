"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password


class TestUserRegistration:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, test_user_data):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test registration with duplicate email."""
        # Create user first
        hashed_password = hash_password(test_user_data["password"])
        existing_user = User(
            email=test_user_data["email"],
            username="differentuser",
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(existing_user)
        await db_session.commit()

        # Try to register with same email
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 409
        data = response.json()
        assert "Email address already registered" in data["detail"]

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test registration with duplicate username."""
        # Create user first
        hashed_password = hash_password(test_user_data["password"])
        existing_user = User(
            email="different@example.com",
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(existing_user)
        await db_session.commit()

        # Try to register with same username
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 409
        data = response.json()
        assert "Username already taken" in data["detail"]

    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        invalid_data = {
            "email": "invalid-email-format",
            "username": "testuser",
            "password": "TestPassword123"
        }
        response = await client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        weak_password_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak"
        }
        response = await client.post("/api/v1/auth/register", json=weak_password_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_register_user_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        incomplete_data = {
            "email": "test@example.com"
            # Missing username and password
        }
        response = await client.post("/api/v1/auth/register", json=incomplete_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestUserLogin:
    """Test user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success_with_username(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test successful login with username."""
        # Create user first
        hashed_password = hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_success_with_email(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test successful login with email."""
        # Create user first
        hashed_password = hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # Login with email
        login_data = {
            "username": test_user_data["email"],  # Using email as username
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_username(self, client: AsyncClient):
        """Test login with non-existent username."""
        login_data = {
            "username": "nonexistent",
            "password": "SomePassword123"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "Invalid username or password" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test login with wrong password."""
        # Create user first
        hashed_password = hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # Try login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "Invalid username or password" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test login with deactivated user account."""
        # Create inactive user
        hashed_password = hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=False  # Inactive user
        )
        db_session.add(user)
        await db_session.commit()

        # Try to login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "Account is deactivated" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login with missing credentials."""
        # Missing password
        incomplete_data = {
            "username": "testuser"
        }
        response = await client.post("/api/v1/auth/login", json=incomplete_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_empty_credentials(self, client: AsyncClient):
        """Test login with empty credentials."""
        empty_data = {
            "username": "",
            "password": ""
        }
        response = await client.post("/api/v1/auth/login", json=empty_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    @pytest.mark.asyncio
    async def test_full_auth_flow(self, client: AsyncClient, test_user_data):
        """Test complete registration -> login flow."""
        # 1. Register user
        register_response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        # 2. Login with registered credentials
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

        # 3. Verify token structure
        token_data = login_response.json()
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert "expires_in" in token_data
        assert token_data["token_type"] == "bearer"
        assert isinstance(token_data["expires_in"], int)
        assert token_data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_duplicate_registration_prevention(self, client: AsyncClient, test_user_data):
        """Test that duplicate registrations are prevented."""
        # Register user first time
        response1 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201

        # Try to register same user again
        response2 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 409

    @pytest.mark.asyncio
    async def test_case_sensitivity_handling(self, client: AsyncClient, test_user_data):
        """Test case sensitivity in usernames and emails."""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Try to login with different case
        login_data = {
            "username": test_user_data["username"].upper(),
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        # Should fail as usernames should be case-sensitive
        assert response.status_code == 401