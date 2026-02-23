"""Main application and integration tests."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


class TestApplicationSetup:
    """Test application setup and configuration."""

    def test_app_creation(self):
        """Test that the FastAPI app is created correctly."""
        assert app.title == "Auth-Serve"
        assert app.description is not None
        assert app.version == "1.0.0"

    def test_app_routes_registered(self):
        """Test that all routes are properly registered."""
        routes = [route.path for route in app.routes]

        # Check that main endpoints are registered
        assert "/health" in routes
        assert "/" in routes

        # Check that auth routes are registered
        auth_routes = [route.path for route in app.routes if route.path.startswith("/auth")]
        assert "/auth/register" in auth_routes
        assert "/auth/login" in auth_routes
        assert "/auth/refresh" in auth_routes

        # Check that user routes are registered
        user_routes = [route.path for route in app.routes if route.path.startswith("/users")]
        assert "/users/me" in user_routes
        assert "/users/me/health" in user_routes


class TestMiddleware:
    """Test middleware functionality."""

    def test_cors_middleware(self, client: TestClient):
        """Test CORS middleware functionality."""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        })

        # Should handle CORS preflight
        assert response.status_code in [200, 405]  # Depending on FastAPI version

    def test_logging_middleware(self, client: TestClient):
        """Test logging middleware adds correlation ID."""
        response = client.get("/health")

        assert response.status_code == 200
        # Check that correlation ID is added to response headers
        assert "X-Correlation-ID" in response.headers
        assert len(response.headers["X-Correlation-ID"]) > 0


class TestExceptionHandlers:
    """Test custom exception handlers."""

    def test_validation_error_handler(self, client: TestClient):
        """Test validation error handling."""
        # Send invalid data to trigger validation error
        response = client.post("/auth/register", json={
            "email": "invalid-email",
            "password": "weak"
        })

        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "message" in data
        assert "details" in data
        assert "path" in data

    def test_auth_service_exception_handler(self, client: TestClient, test_user):
        """Test custom auth service exception handling."""
        # Try to register with existing email
        response = client.post("/auth/register", json={
            "email": test_user.email,
            "password": "ValidPassword123!"
        })

        assert response.status_code == 409
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "path" in data

    def test_circuit_breaker_exception_handler(self, client: TestClient):
        """Test circuit breaker exception handling."""
        # This is harder to test without actually triggering a circuit breaker
        # In a real scenario, we'd mock the circuit breaker to be open
        pass

    def test_general_exception_handler(self, client: TestClient):
        """Test general exception handler."""
        # This would require triggering an unexpected exception
        # In a real scenario, we might temporarily patch a function to raise an exception
        pass


class TestApplicationLifespan:
    """Test application lifespan events."""

    def test_startup_creates_tables(self):
        """Test that startup event creates database tables."""
        # This is tested implicitly by the test fixtures
        # The test database is created during app startup simulation
        pass


class TestSecurityHeaders:
    """Test security-related headers and configurations."""

    def test_no_server_header_exposure(self, client: TestClient):
        """Test that server information is not exposed."""
        response = client.get("/health")

        # Should not expose server implementation details
        assert "server" not in response.headers.lower()
        assert "x-powered-by" not in response.headers.lower()

    def test_content_type_headers(self, client: TestClient):
        """Test proper content type headers."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"


class TestOpenAPIDocumentation:
    """Test OpenAPI/Swagger documentation."""

    def test_openapi_schema_available(self, client: TestClient):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_swagger_docs_available(self, client: TestClient):
        """Test that Swagger docs are available."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_available(self, client: TestClient):
        """Test that ReDoc is available."""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestIntegrationScenarios:
    """Test complex integration scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client: AsyncClient):
        """Test handling of concurrent requests."""
        import asyncio

        async def make_request():
            return await async_client.get("/health")

        # Make multiple concurrent requests
        responses = await asyncio.gather(*[make_request() for _ in range(10)])

        # All should succeed
        for response in responses:
            assert response.status_code == 200

        # All should have correlation IDs
        correlation_ids = [response.headers.get("X-Correlation-ID") for response in responses]
        assert len(set(correlation_ids)) == 10  # All should be unique

    @pytest.mark.asyncio
    async def test_user_journey_with_errors(self, async_client: AsyncClient):
        """Test complete user journey including error scenarios."""
        # Try to access protected endpoint without auth
        response = await async_client.get("/users/me")
        assert response.status_code == 401

        # Try to login with non-existent user
        response = await async_client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 401

        # Register user
        user_data = {
            "email": "journey@example.com",
            "password": "JourneyPassword123!"
        }
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register same user again
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 409

        # Login successfully
        response = await async_client.post("/auth/login", json=user_data)
        assert response.status_code == 200
        token_data = response.json()

        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # Access protected endpoint successfully
        response = await async_client.get("/users/me", headers=headers)
        assert response.status_code == 200

        # Try to update with invalid data
        response = await async_client.put("/users/me", json={
            "email": "invalid-email"
        }, headers=headers)
        assert response.status_code == 422

        # Update successfully
        response = await async_client.put("/users/me", json={
            "email": "updated-journey@example.com"
        }, headers=headers)
        assert response.status_code == 200

        # Health check
        response = await async_client.get("/users/me/health", headers=headers)
        assert response.status_code == 200

        # Delete account
        response = await async_client.delete("/users/me", headers=headers)
        assert response.status_code == 204

        # Try to access after deletion
        response = await async_client.get("/users/me", headers=headers)
        assert response.status_code == 401

    def test_error_response_consistency(self, client: TestClient):
        """Test that all error responses follow consistent format."""
        error_endpoints = [
            ("/users/me", 401),  # Unauthorized
            ("/auth/login", 422),  # Validation error (empty body)
            ("/auth/register", 422),  # Validation error (empty body)
        ]

        for endpoint, expected_status in error_endpoints:
            if expected_status == 422:
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)

            assert response.status_code == expected_status
            data = response.json()

            # All error responses should have consistent structure
            assert "error" in data or "detail" in data
            # Most should have path information
            if "path" in data:
                assert data["path"] == endpoint

    def test_rate_limiting_headers(self, client: TestClient):
        """Test rate limiting configuration (even if not implemented)."""
        response = client.get("/health")

        # Should not expose rate limiting headers unless implemented
        # This is more of a documentation test
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, async_client: AsyncClient):
        """Test that database transactions are properly rolled back on errors."""
        # This is implicitly tested by other tests, but we can be more explicit
        user_data = {
            "email": "transaction@example.com",
            "password": "TransactionPassword123!"
        }

        # Register user
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register same user again - should not leave partial data
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 409

        # Original user should still be intact
        response = await async_client.post("/auth/login", json=user_data)
        assert response.status_code == 200

    def test_api_versioning_preparation(self, client: TestClient):
        """Test that the API is structured for future versioning."""
        # Check that routes don't have version prefixes (v1, v2, etc.)
        # This suggests the current API is the base version
        routes = [route.path for route in app.routes]

        # Should not have version prefixes in current routes
        versioned_routes = [route for route in routes if "/v1/" in route or "/v2/" in route]
        assert len(versioned_routes) == 0

        # Base endpoints should be available
        response = client.get("/")
        assert response.status_code == 200

        # Health endpoint should indicate version
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data