"""Integration tests for authentication routes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.user_service import UserService
from app.utils.password import hash_password


class TestAuthRoutes:
    """Test authentication endpoints."""

    def test_register_endpoint_success(self, test_client: TestClient):
        """Test successful user registration endpoint."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepass123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_endpoint_invalid_email(self, test_client: TestClient):
        """Test registration with invalid email."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "username": "newuser",
                "password": "securepass123",
            },
        )
        assert response.status_code == 422

    def test_register_endpoint_short_password(self, test_client: TestClient):
        """Test registration with short password."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "short",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "VALIDATION_ERROR"

    def test_register_endpoint_duplicate_email(self, test_client: TestClient):
        """Test registration with duplicate email."""
        test_client.post(
            "/auth/register",
            json={
                "email": "existing@example.com",
                "username": "user1",
                "password": "securepass123",
            },
        )
        response = test_client.post(
            "/auth/register",
            json={
                "email": "existing@example.com",
                "username": "user2",
                "password": "securepass123",
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "USER_ALREADY_EXISTS"

    def test_register_endpoint_duplicate_username(self, test_client: TestClient):
        """Test registration with duplicate username."""
        test_client.post(
            "/auth/register",
            json={
                "email": "user1@example.com",
                "username": "duplicate",
                "password": "securepass123",
            },
        )
        response = test_client.post(
            "/auth/register",
            json={
                "email": "user2@example.com",
                "username": "duplicate",
                "password": "securepass123",
            },
        )
        assert response.status_code == 409

    def test_login_endpoint_with_email_success(self, test_client: TestClient):
        """Test successful login with email."""
        # Register
        test_client.post(
            "/auth/register",
            json={
                "email": "testuser@example.com",
                "username": "testuser",
                "password": "securepass123",
            },
        )
        # Login
        response = test_client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "securepass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "testuser@example.com"

    def test_login_endpoint_with_username_success(self, test_client: TestClient):
        """Test successful login with username."""
        # Register
        test_client.post(
            "/auth/register",
            json={
                "email": "testuser@example.com",
                "username": "testuser",
                "password": "securepass123",
            },
        )
        # Login
        response = test_client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "securepass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "testuser"

    def test_login_endpoint_wrong_password(self, test_client: TestClient):
        """Test login with wrong password."""
        test_client.post(
            "/auth/register",
            json={
                "email": "testuser@example.com",
                "username": "testuser",
                "password": "securepass123",
            },
        )
        response = test_client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_login_endpoint_nonexistent_user(self, test_client: TestClient):
        """Test login for non-existent user."""
        response = test_client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )
        assert response.status_code == 401

    def test_login_endpoint_missing_credentials(self, test_client: TestClient):
        """Test login with missing credentials."""
        response = test_client.post(
            "/auth/login",
            json={
                "password": "securepass123",
            },
        )
        assert response.status_code == 401

    def test_login_endpoint_missing_password(self, test_client: TestClient):
        """Test login with missing password."""
        response = test_client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
            },
        )
        assert response.status_code == 401

    def test_refresh_endpoint_success(self, test_client: TestClient):
        """Test successful token refresh."""
        register_response = test_client.post(
            "/auth/register",
            json={
                "email": "testuser@example.com",
                "username": "testuser",
                "password": "securepass123",
            },
        )
        register_data = register_response.json()
        refresh_token = register_data["refresh_token"]

        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == refresh_token
        assert data["user"]["username"] == "testuser"

    def test_refresh_endpoint_invalid_token(self, test_client: TestClient):
        """Test token refresh with invalid token."""
        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_response_has_request_id(self, test_client: TestClient):
        """Test that responses include X-Request-ID header."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "testuser@example.com",
                "username": "testuser",
                "password": "securepass123",
            },
        )
        assert "x-request-id" in response.headers

    def test_error_response_format(self, test_client: TestClient):
        """Test error response has correct format."""
        response = test_client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "error_code" in data
        assert "timestamp" in data
        assert "request_id" in data

    def test_login_case_insensitive_email(self, test_client: TestClient):
        """Test login works with different email case."""
        test_client.post(
            "/auth/register",
            json={
                "email": "TestUser@Example.Com",
                "username": "testuser",
                "password": "securepass123",
            },
        )
        response = test_client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "securepass123",
            },
        )
        assert response.status_code == 200

    def test_register_response_includes_user_info(self, test_client: TestClient):
        """Test registration response includes complete user info."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepass123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        user = data["user"]
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "is_active" in user
        assert "created_at" in user
        assert user["is_active"] is True
