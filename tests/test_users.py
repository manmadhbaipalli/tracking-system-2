"""User management endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestUserProfile:
    """Test user profile endpoint."""

    def test_get_profile_success(self, client: TestClient, auth_headers: dict):
        """Test successful profile retrieval."""
        response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["is_active"] is True
        assert "hashed_password" not in data

    def test_get_profile_unauthorized(self, client: TestClient):
        """Test profile access without authentication fails."""
        response = client.get("/users/me")

        assert response.status_code == 401

    def test_get_profile_invalid_token(self, client: TestClient):
        """Test profile access with invalid token fails."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/users/me", headers=headers)

        assert response.status_code == 401

    def test_get_profile_malformed_token(self, client: TestClient):
        """Test profile access with malformed token fails."""
        headers = {"Authorization": "invalid-format"}
        response = client.get("/users/me", headers=headers)

        assert response.status_code == 401

    def test_get_profile_inactive_user(self, client: TestClient, inactive_user: User):
        """Test profile access for inactive user fails."""
        from app.core.security import create_access_token
        from datetime import timedelta

        # Create token for inactive user
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": inactive_user.email}, expires_delta=access_token_expires
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/users/me", headers=headers)

        assert response.status_code == 400
        data = response.json()
        assert "inactive" in data["detail"].lower()


class TestUserProfileUpdate:
    """Test user profile update endpoint."""

    def test_update_email_success(self, client: TestClient, auth_headers: dict):
        """Test successful email update."""
        update_data = {"email": "updated@example.com"}

        response = client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert "id" in data
        assert "updated_at" in data

    def test_update_password_success(self, client: TestClient, auth_headers: dict):
        """Test successful password update."""
        update_data = {"password": "NewPassword123!"}

        response = client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

        # Verify new password works by trying to login
        login_data = {
            "email": data["email"],
            "password": "NewPassword123!",
        }
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200

    def test_update_is_active_success(self, client: TestClient, auth_headers: dict):
        """Test successful is_active update."""
        update_data = {"is_active": False}

        response = client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_update_multiple_fields(self, client: TestClient, auth_headers: dict):
        """Test updating multiple fields at once."""
        update_data = {
            "email": "multiupdate@example.com",
            "password": "MultiPassword123!",
            "is_active": True,
        }

        response = client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "multiupdate@example.com"
        assert data["is_active"] is True

    def test_update_empty_payload(self, client: TestClient, auth_headers: dict):
        """Test update with empty payload."""
        response = client.put("/users/me", json={}, headers=auth_headers)

        assert response.status_code == 200
        # Should return current user data unchanged

    def test_update_null_values(self, client: TestClient, auth_headers: dict):
        """Test update with null values."""
        update_data = {
            "email": None,
            "password": None,
            "is_active": None,
        }

        response = client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        # Should return current user data unchanged

    def test_update_invalid_email(self, client: TestClient, auth_headers: dict):
        """Test update with invalid email format."""
        update_data = {"email": "invalid-email-format"}

        response = client.put("/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 422

    def test_update_weak_password(self, client: TestClient, auth_headers: dict):
        """Test update with weak password."""
        weak_passwords = [
            "weak",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoDigitsHere!",  # No digits
            "NoSpecialChars123",  # No special chars
        ]

        for weak_password in weak_passwords:
            update_data = {"password": weak_password}
            response = client.put("/users/me", json=update_data, headers=auth_headers)
            assert response.status_code == 422

    def test_update_unauthorized(self, client: TestClient):
        """Test profile update without authentication fails."""
        update_data = {"email": "unauthorized@example.com"}

        response = client.put("/users/me", json=update_data)

        assert response.status_code == 401

    def test_update_invalid_token(self, client: TestClient):
        """Test profile update with invalid token fails."""
        headers = {"Authorization": "Bearer invalid-token"}
        update_data = {"email": "invalid@example.com"}

        response = client.put("/users/me", json=update_data, headers=headers)

        assert response.status_code == 401


class TestUserAccountDeletion:
    """Test user account deletion endpoint."""

    def test_delete_account_success(self, client: TestClient, auth_headers: dict):
        """Test successful account deletion."""
        response = client.delete("/users/me", headers=auth_headers)

        assert response.status_code == 204

        # Verify user can no longer access profile
        profile_response = client.get("/users/me", headers=auth_headers)
        assert profile_response.status_code == 401

        # Verify user can no longer login
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        }
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 401

    def test_delete_account_unauthorized(self, client: TestClient):
        """Test account deletion without authentication fails."""
        response = client.delete("/users/me")

        assert response.status_code == 401

    def test_delete_account_invalid_token(self, client: TestClient):
        """Test account deletion with invalid token fails."""
        headers = {"Authorization": "Bearer invalid-token"}

        response = client.delete("/users/me", headers=headers)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_account_flow(self, async_client: AsyncClient):
        """Test complete account deletion flow."""
        # Register a user
        user_data = {
            "email": "deletetest@example.com",
            "password": "DeletePassword123!",
        }

        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Login to get token
        login_response = await async_client.post("/auth/login", json=user_data)
        assert login_response.status_code == 200

        token_data = login_response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # Verify profile access works
        profile_response = await async_client.get("/users/me", headers=headers)
        assert profile_response.status_code == 200

        # Delete account
        delete_response = await async_client.delete("/users/me", headers=headers)
        assert delete_response.status_code == 204

        # Verify profile access no longer works
        profile_response2 = await async_client.get("/users/me", headers=headers)
        assert profile_response2.status_code == 401

        # Verify login no longer works
        login_response2 = await async_client.post("/auth/login", json=user_data)
        assert login_response2.status_code == 401


class TestUserHealthCheck:
    """Test user health check endpoint."""

    def test_user_health_check_success(self, client: TestClient, auth_headers: dict):
        """Test successful user health check."""
        response = client.get("/users/me/health", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "user_id" in data
        assert data["is_active"] is True
        assert data["authenticated"] is True

    def test_user_health_check_unauthorized(self, client: TestClient):
        """Test user health check without authentication fails."""
        response = client.get("/users/me/health")

        assert response.status_code == 401

    def test_user_health_check_invalid_token(self, client: TestClient):
        """Test user health check with invalid token fails."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/users/me/health", headers=headers)

        assert response.status_code == 401

    def test_user_health_check_inactive_user(self, client: TestClient, inactive_user: User):
        """Test user health check for inactive user fails."""
        from app.core.security import create_access_token
        from datetime import timedelta

        # Create token for inactive user
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": inactive_user.email}, expires_delta=access_token_expires
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/users/me/health", headers=headers)

        assert response.status_code == 400
        data = response.json()
        assert "inactive" in data["detail"].lower()


class TestUserIntegration:
    """Test user management integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, async_client: AsyncClient):
        """Test complete user lifecycle: register, login, update, delete."""
        # Register
        user_data = {
            "email": "lifecycle@example.com",
            "password": "LifecyclePassword123!",
        }

        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Login
        login_response = await async_client.post("/auth/login", json=user_data)
        assert login_response.status_code == 200

        token_data = login_response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # Get profile
        profile_response = await async_client.get("/users/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == user_data["email"]

        # Update profile
        update_data = {
            "email": "updated-lifecycle@example.com",
            "password": "UpdatedPassword123!",
        }

        update_response = await async_client.put("/users/me", json=update_data, headers=headers)
        assert update_response.status_code == 200
        updated_profile = update_response.json()
        assert updated_profile["email"] == update_data["email"]

        # Verify old password doesn't work
        old_login_data = {
            "email": update_data["email"],
            "password": user_data["password"],
        }
        old_login_response = await async_client.post("/auth/login", json=old_login_data)
        assert old_login_response.status_code == 401

        # Verify new password works
        new_login_data = {
            "email": update_data["email"],
            "password": update_data["password"],
        }
        new_login_response = await async_client.post("/auth/login", json=new_login_data)
        assert new_login_response.status_code == 200

        # Delete account
        delete_response = await async_client.delete("/users/me", headers=headers)
        assert delete_response.status_code == 204

        # Verify account is gone
        final_login_response = await async_client.post("/auth/login", json=new_login_data)
        assert final_login_response.status_code == 401

    def test_concurrent_user_operations(self, client: TestClient):
        """Test that user operations maintain data consistency."""
        # Register multiple users with similar data
        for i in range(3):
            user_data = {
                "email": f"concurrent{i}@example.com",
                "password": "ConcurrentPassword123!",
            }

            response = client.post("/auth/register", json=user_data)
            assert response.status_code == 201

            # Login and verify profile
            login_response = client.post("/auth/login", json=user_data)
            assert login_response.status_code == 200

            token_data = login_response.json()
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}

            profile_response = client.get("/users/me", headers=headers)
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            assert profile_data["email"] == user_data["email"]

    def test_user_session_management(self, client: TestClient, test_user: User):
        """Test that user sessions are properly managed."""
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!",
        }

        # Login multiple times to get different tokens
        login1 = client.post("/auth/login", json=login_data)
        assert login1.status_code == 200
        token1 = login1.json()["access_token"]

        login2 = client.post("/auth/login", json=login_data)
        assert login2.status_code == 200
        token2 = login2.json()["access_token"]

        # Both tokens should work independently
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        response1 = client.get("/users/me", headers=headers1)
        assert response1.status_code == 200

        response2 = client.get("/users/me", headers=headers2)
        assert response2.status_code == 200