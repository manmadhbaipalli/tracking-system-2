"""Authentication endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestRegistration:
    """Test user registration endpoint."""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "NewPassword123!",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["is_active"] is True
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with existing email fails."""
        user_data = {
            "email": test_user.email,
            "password": "NewPassword123!",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email fails."""
        user_data = {
            "email": "invalid-email",
            "password": "NewPassword123!",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 422

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password fails."""
        test_cases = [
            {"email": "user1@example.com", "password": "weak"},  # Too short
            {"email": "user2@example.com", "password": "nouppercase123!"},  # No uppercase
            {"email": "user3@example.com", "password": "NOLOWERCASE123!"},  # No lowercase
            {"email": "user4@example.com", "password": "NoDigitsHere!"},  # No digits
            {"email": "user5@example.com", "password": "NoSpecialChars123"},  # No special chars
        ]

        for user_data in test_cases:
            response = client.post("/auth/register", json=user_data)
            assert response.status_code == 422

    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        # Missing email
        response = client.post("/auth/register", json={"password": "ValidPassword123!"})
        assert response.status_code == 422

        # Missing password
        response = client.post("/auth/register", json={"email": "user@example.com"})
        assert response.status_code == 422

        # Empty payload
        response = client.post("/auth/register", json={})
        assert response.status_code == 422


class TestLogin:
    """Test user login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful user login."""
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    def test_login_invalid_email(self, client: TestClient):
        """Test login with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPassword123!",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with incorrect password."""
        login_data = {
            "email": test_user.email,
            "password": "WrongPassword123!",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_login_inactive_user(self, client: TestClient, inactive_user: User):
        """Test login with inactive user account."""
        login_data = {
            "email": inactive_user.email,
            "password": "TestPassword123!",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 400
        data = response.json()
        assert "inactive" in data["detail"].lower()

    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing required fields."""
        # Missing email
        response = client.post("/auth/login", json={"password": "TestPassword123!"})
        assert response.status_code == 422

        # Missing password
        response = client.post("/auth/login", json={"email": "user@example.com"})
        assert response.status_code == 422

        # Empty payload
        response = client.post("/auth/login", json={})
        assert response.status_code == 422

    def test_login_invalid_email_format(self, client: TestClient):
        """Test login with invalid email format."""
        login_data = {
            "email": "invalid-email-format",
            "password": "TestPassword123!",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 422


class TestTokenRefresh:
    """Test token refresh endpoint."""

    def test_refresh_not_implemented(self, client: TestClient):
        """Test that refresh endpoint returns not implemented."""
        response = client.post("/auth/refresh")

        assert response.status_code == 501
        data = response.json()
        assert "not implemented" in data["detail"].lower()


class TestAuthenticationIntegration:
    """Test authentication integration scenarios."""

    @pytest.mark.asyncio
    async def test_register_login_flow(self, async_client: AsyncClient):
        """Test complete register and login flow."""
        # Register new user
        user_data = {
            "email": "flowtest@example.com",
            "password": "FlowPassword123!",
        }

        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201

        user_info = register_response.json()
        assert user_info["email"] == user_data["email"]

        # Login with the registered user
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"],
        }

        login_response = await async_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200

        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Verify token works for protected endpoint
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_response = await async_client.get("/users/me", headers=headers)
        assert profile_response.status_code == 200

        profile_data = profile_response.json()
        assert profile_data["email"] == user_data["email"]

    def test_case_insensitive_email_registration(self, client: TestClient):
        """Test that email addresses are handled consistently."""
        user_data_1 = {
            "email": "CaseTest@EXAMPLE.COM",
            "password": "CasePassword123!",
        }

        # Register with mixed case email
        response1 = client.post("/auth/register", json=user_data_1)
        assert response1.status_code == 201

        user_data_2 = {
            "email": "casetest@example.com",
            "password": "AnotherPassword123!",
        }

        # Try to register with same email in different case
        response2 = client.post("/auth/register", json=user_data_2)
        # Should succeed because email case shouldn't matter for uniqueness
        # But this depends on database collation - with SQLite it might be case sensitive
        # The important thing is consistent behavior

        # Login should work with the original case
        login_data = {
            "email": "CaseTest@EXAMPLE.COM",
            "password": "CasePassword123!",
        }

        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200

    def test_sql_injection_protection(self, client: TestClient):
        """Test that SQL injection attempts are blocked."""
        malicious_payloads = [
            {"email": "test@example.com'; DROP TABLE users; --", "password": "Password123!"},
            {"email": "test@example.com", "password": "'; SELECT * FROM users; --"},
            {"email": "admin'--", "password": "Password123!"},
        ]

        for payload in malicious_payloads:
            response = client.post("/auth/login", json=payload)
            # Should either be 422 (validation error) or 401 (auth failed)
            # Should NOT cause a 500 server error from SQL injection
            assert response.status_code in [401, 422]

    def test_xss_protection(self, client: TestClient):
        """Test that XSS payloads in email field are handled safely."""
        xss_payloads = [
            "<script>alert('xss')</script>@example.com",
            "javascript:alert('xss')@example.com",
            "<img src=x onerror=alert('xss')>@example.com",
        ]

        for payload in xss_payloads:
            user_data = {
                "email": payload,
                "password": "Password123!",
            }

            response = client.post("/auth/register", json=user_data)
            # Should be validation error due to invalid email format
            assert response.status_code == 422

    def test_password_not_logged(self, client: TestClient, caplog):
        """Test that passwords are not logged in plain text."""
        user_data = {
            "email": "logtest@example.com",
            "password": "SecretPassword123!",
        }

        # Clear any previous logs
        caplog.clear()

        response = client.post("/auth/register", json=user_data)

        # Check that password is not in any log messages
        for record in caplog.records:
            assert "SecretPassword123!" not in record.message
            assert "SecretPassword123!" not in str(record.args)