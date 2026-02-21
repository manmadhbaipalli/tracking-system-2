"""Tests for user management endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token


class TestUsersEndpoints:
    """Test cases for user management endpoints."""

    def test_get_current_user_success(self, test_client: TestClient, test_user_data):
        """Test getting current user profile with valid token."""
        # First register a user
        register_response = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        # Login to get token
        login_response = test_client.post("/api/v1/auth/login", json=test_user_data)
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Get current user profile
        headers = {"Authorization": f"Bearer {access_token}"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "created_at" in data
        assert "is_active" in data
        assert data["is_active"] is True
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_current_user_missing_token(self, test_client: TestClient):
        """Test getting current user without authentication token."""
        response = test_client.get("/api/v1/users/me")
        assert response.status_code == 403  # Forbidden due to missing token

    def test_get_current_user_invalid_token(self, test_client: TestClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Could not validate credentials" in data["detail"]

    def test_get_current_user_expired_token(self, test_client: TestClient, test_user_data):
        """Test getting current user with expired token."""
        from datetime import datetime, timedelta

        # Create an expired token
        expired_token = create_access_token(
            subject=test_user_data["email"],
            expires_delta=timedelta(seconds=-1)  # Expired 1 second ago
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401

    def test_get_current_user_malformed_token(self, test_client: TestClient):
        """Test getting current user with malformed bearer token."""
        # Missing 'Bearer' prefix
        headers = {"Authorization": "malformed-token"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 403

        # Wrong scheme
        headers = {"Authorization": "Basic malformed-token"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 403

    def test_get_current_user_nonexistent_user_in_token(self, test_client: TestClient):
        """Test getting current user when user in token doesn't exist."""
        # Create token for nonexistent user
        token = create_access_token(subject="nonexistent@example.com")

        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "User not found" in data["detail"]

    def test_get_current_user_content_type(self, test_client: TestClient, test_user_data):
        """Test that users endpoint returns JSON content type."""
        # Register and login
        register_response = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        login_response = test_client.post("/api/v1/auth/login", json=test_user_data)
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Test content type
        headers = {"Authorization": f"Bearer {access_token}"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert "application/json" in response.headers.get("content-type", "")

    def test_users_endpoint_cors_headers(self, test_client: TestClient, test_user_data):
        """Test that users endpoint has proper CORS configuration."""
        # Register and login
        register_response = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        login_response = test_client.post("/api/v1/auth/login", json=test_user_data)
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # Test endpoint accessibility (CORS handled by middleware)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = test_client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200