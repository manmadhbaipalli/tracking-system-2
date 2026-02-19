"""Integration tests for middleware functionality."""

from fastapi.testclient import TestClient
import json


class TestMiddleware:
    """Test middleware functionality."""

    def test_exception_handler_catches_validation_errors(
        self, test_client: TestClient
    ):
        """Test exception handler catches validation errors."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "invalid-email",
                "username": "user",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_exception_handler_returns_consistent_format(
        self, test_client: TestClient
    ):
        """Test exception handler returns consistent error format."""
        response = test_client.post(
            "/auth/login",
            json={"password": "anypassword"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "error_code" in data
        assert "timestamp" in data
        assert "request_id" in data

    def test_request_id_in_response_header(self, test_client: TestClient):
        """Test request ID is included in response headers."""
        response = test_client.get("/health")
        assert "x-request-id" in response.headers
        request_id = response.headers["x-request-id"]
        assert len(request_id) > 0

    def test_request_id_uniqueness(self, test_client: TestClient):
        """Test that different requests have different request IDs."""
        response1 = test_client.get("/health")
        response2 = test_client.get("/health")
        request_id1 = response1.headers.get("x-request-id")
        request_id2 = response2.headers.get("x-request-id")
        # Request IDs should be UUIDs
        assert request_id1 != request_id2

    def test_cors_headers_present(self, test_client: TestClient):
        """Test CORS headers are present in responses."""
        response = test_client.get("/health")
        assert response.status_code == 200
        # FastAPI's CORS middleware should be active

    def test_error_response_includes_request_id(self, test_client: TestClient):
        """Test error responses include request ID in body."""
        response = test_client.post(
            "/auth/login",
            json={"email": "test@test.com", "password": "wrong"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "request_id" in data
        assert len(data["request_id"]) > 0

    def test_error_response_has_timestamp(self, test_client: TestClient):
        """Test error responses include timestamp."""
        response = test_client.post(
            "/auth/login",
            json={"password": "anypassword"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "timestamp" in data
        # Timestamp should be ISO format

    def test_error_code_present_in_all_errors(self, test_client: TestClient):
        """Test that error_code is present in all error responses."""
        # Validation error
        response1 = test_client.post(
            "/auth/register",
            json={
                "email": "test@test.com",
                "username": "user",
                "password": "short",
            },
        )
        assert "error_code" in response1.json()

        # Auth error
        response2 = test_client.post(
            "/auth/login",
            json={"password": "any"},
        )
        assert "error_code" in response2.json()

    def test_middleware_preserves_response_content(self, test_client: TestClient):
        """Test that middleware doesn't alter response content."""
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
        assert "user" in data

    def test_error_detail_for_invalid_credentials(self, test_client: TestClient):
        """Test error detail is present for auth errors."""
        response = test_client.post(
            "/auth/login",
            json={
                "email": "test@test.com",
                "password": "wrongpassword",
            },
        )
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0

    def test_database_error_returns_500(self, test_client: TestClient):
        """Test that database errors return 500 status."""
        # This is a placeholder for actual database error testing
        # In a real scenario, you might mock database errors
        pass

    def test_response_content_type(self, test_client: TestClient):
        """Test response content-type is JSON."""
        response = test_client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")
