"""Tests for user management endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password, create_access_token


class TestUserProfile:
    """Test user profile endpoint."""

    async def _create_user_and_token(self, db_session: AsyncSession, user_data: dict) -> tuple[User, str]:
        """Helper method to create a user and authentication token."""
        hashed_password = hash_password(user_data["password"])
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create access token
        access_token = create_access_token(data={"sub": user.username})

        return user, access_token

    @pytest.mark.asyncio
    async def test_get_current_user_profile_success(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test successfully retrieving current user profile."""
        user, token = await self._create_user_and_token(db_session, test_user_data)

        # Request profile with valid token
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure and data
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["username"] == user.username
        assert data["is_active"] == user.is_active
        assert "created_at" in data
        assert "updated_at" in data

        # Ensure password is not included in response
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_profile_no_token(self, client: AsyncClient):
        """Test accessing profile without authentication token."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_current_user_profile_invalid_token(self, client: AsyncClient):
        """Test accessing profile with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "Could not validate credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_profile_malformed_token(self, client: AsyncClient):
        """Test accessing profile with malformed authorization header."""
        # Missing Bearer prefix
        headers = {"Authorization": "invalid_token_format"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_current_user_profile_expired_token(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test accessing profile with expired token."""
        user, _ = await self._create_user_and_token(db_session, test_user_data)

        # Create an expired token (negative expiration)
        from datetime import timedelta
        expired_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(seconds=-1)
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "Could not validate credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_profile_inactive_user(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test accessing profile with deactivated user."""
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
        await db_session.refresh(user)

        # Create token for inactive user
        access_token = create_access_token(data={"sub": user.username})

        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "Could not validate credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_profile_nonexistent_user_token(self, client: AsyncClient):
        """Test accessing profile with token for non-existent user."""
        # Create token for non-existent user
        access_token = create_access_token(data={"sub": "nonexistent_user"})

        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "Could not validate credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_profile_token_without_subject(self, client: AsyncClient):
        """Test accessing profile with token missing subject claim."""
        # Create token without 'sub' field
        access_token = create_access_token(data={"user_id": 123})  # Wrong field name

        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "Could not validate credentials" in data["detail"]


class TestUserAuthIntegration:
    """Integration tests for user endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_full_user_flow_with_auth(self, client: AsyncClient, test_user_data):
        """Test complete user flow: register -> login -> get profile."""
        # 1. Register user
        register_response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        # 2. Login to get token
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        token_data = login_response.json()

        # 3. Get user profile with token
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_response = await client.get("/api/v1/users/me", headers=headers)
        assert profile_response.status_code == 200

        # 4. Verify profile data matches registration
        profile_data = profile_response.json()
        assert profile_data["email"] == test_user_data["email"]
        assert profile_data["username"] == test_user_data["username"]
        assert profile_data["is_active"] is True

    @pytest.mark.asyncio
    async def test_user_profile_data_consistency(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test that profile data is consistent with database."""
        user, token = await self._create_user_and_token(db_session, test_user_data)

        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify all fields match database
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["username"] == user.username
        assert data["is_active"] == user.is_active
        # Note: datetime comparison would require parsing, so we just check presence
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    async def _create_user_and_token(self, db_session: AsyncSession, user_data: dict) -> tuple[User, str]:
        """Helper method to create a user and authentication token."""
        hashed_password = hash_password(user_data["password"])
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create access token
        access_token = create_access_token(data={"sub": user.username})

        return user, access_token


class TestUserEndpointSecurity:
    """Security-focused tests for user endpoints."""

    @pytest.mark.asyncio
    async def test_profile_endpoint_requires_authentication(self, client: AsyncClient):
        """Test that profile endpoint properly requires authentication."""
        # No Authorization header
        response1 = await client.get("/api/v1/users/me")
        assert response1.status_code == 401

        # Empty Authorization header
        headers2 = {"Authorization": ""}
        response2 = await client.get("/api/v1/users/me", headers=headers2)
        assert response2.status_code == 401

        # Invalid Authorization scheme
        headers3 = {"Authorization": "Basic sometoken"}
        response3 = await client.get("/api/v1/users/me", headers=headers3)
        assert response3.status_code == 401

    @pytest.mark.asyncio
    async def test_profile_does_not_leak_sensitive_data(self, client: AsyncClient, test_user_data, db_session: AsyncSession):
        """Test that profile endpoint doesn't expose sensitive information."""
        user, token = await self._create_user_and_token(db_session, test_user_data)

        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Ensure sensitive fields are not included
        sensitive_fields = [
            "password", "hashed_password", "secret", "private_key",
            "token", "session", "salt"
        ]
        for field in sensitive_fields:
            assert field not in data

    async def _create_user_and_token(self, db_session: AsyncSession, user_data: dict) -> tuple[User, str]:
        """Helper method to create a user and authentication token."""
        hashed_password = hash_password(user_data["password"])
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create access token
        access_token = create_access_token(data={"sub": user.username})

        return user, access_token