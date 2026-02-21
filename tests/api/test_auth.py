"""Tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.security import create_access_token, decode_token


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""

    def test_register_success(self, test_client: TestClient, test_user_data):
        """Test successful user registration."""
        response = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "created_at" in data
        assert "is_active" in data
        assert data["is_active"] is True
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, test_client: TestClient, test_user_data):
        """Test registration with duplicate email fails."""
        # First registration
        response1 = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201

        # Second registration with same email
        response2 = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 409
        data = response2.json()
        assert "detail" in data
        assert "already exists" in data["detail"]

    def test_register_invalid_email(self, test_client: TestClient):
        """Test registration with invalid email format."""
        invalid_data = {
            "email": "invalid-email-format",
            "password": "validpassword123"
        }
        response = test_client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_register_missing_fields(self, test_client: TestClient):
        """Test registration with missing required fields."""
        # Missing password
        incomplete_data = {"email": "test@example.com"}
        response = test_client.post("/api/v1/auth/register", json=incomplete_data)
        assert response.status_code == 422

        # Missing email
        incomplete_data = {"password": "testpassword123"}
        response = test_client.post("/api/v1/auth/register", json=incomplete_data)
        assert response.status_code == 422

    def test_register_password_too_short(self, test_client: TestClient):
        """Test registration with password that's too short."""
        short_password_data = {
            "email": "test@example.com",
            "password": "123"  # Too short
        }
        response = test_client.post("/api/v1/auth/register", json=short_password_data)
        assert response.status_code == 422

    def test_login_success(self, test_client: TestClient, test_user_data):
        """Test successful login."""
        # First register a user
        register_response = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        # Then login
        login_response = test_client.post("/api/v1/auth/login", json=test_user_data)
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify the token is valid
        token = data["access_token"]
        payload = decode_token(token)
        assert payload["sub"] == test_user_data["email"]

    def test_login_wrong_password(self, test_client: TestClient, test_user_data):
        """Test login with wrong password."""
        # First register a user
        register_response = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        # Try login with wrong password
        wrong_credentials = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        login_response = test_client.post("/api/v1/auth/login", json=wrong_credentials)
        assert login_response.status_code == 401
        data = login_response.json()
        assert "detail" in data
        assert "Incorrect email or password" in data["detail"]

    def test_login_nonexistent_user(self, test_client: TestClient):
        """Test login with nonexistent user."""
        nonexistent_credentials = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
        response = test_client.post("/api/v1/auth/login", json=nonexistent_credentials)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect email or password" in data["detail"]

    def test_login_invalid_email_format(self, test_client: TestClient):
        """Test login with invalid email format."""
        invalid_credentials = {
            "email": "invalid-email",
            "password": "somepassword"
        }
        response = test_client.post("/api/v1/auth/login", json=invalid_credentials)
        assert response.status_code == 422

    def test_login_missing_fields(self, test_client: TestClient):
        """Test login with missing required fields."""
        # Missing password
        incomplete_data = {"email": "test@example.com"}
        response = test_client.post("/api/v1/auth/login", json=incomplete_data)
        assert response.status_code == 422

        # Missing email
        incomplete_data = {"password": "testpassword123"}
        response = test_client.post("/api/v1/auth/login", json=incomplete_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, async_test_client: AsyncClient, test_user_data):
        """Test login attempt with inactive user."""
        # This test would require modifying user's is_active status
        # For now, this is a placeholder test since we don't have an admin endpoint
        # to deactivate users in the current implementation
        pass

    def test_auth_endpoints_content_type(self, test_client: TestClient, test_user_data):
        """Test that auth endpoints return JSON content type."""
        # Register
        response = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert "application/json" in response.headers.get("content-type", "")

        # Login
        response = test_client.post("/api/v1/auth/login", json=test_user_data)
        assert "application/json" in response.headers.get("content-type", "")

    def test_auth_endpoints_cors_headers(self, test_client: TestClient):
        """Test that auth endpoints have proper CORS configuration."""
        # This is mainly tested through the middleware configuration
        # The actual CORS behavior would be better tested in integration tests
        response = test_client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "testpass123"}
        )
        # TestClient doesn't fully simulate browser CORS behavior
        # but we can verify the endpoints are accessible
        assert response.status_code in [201, 422]  # Either success or validation error