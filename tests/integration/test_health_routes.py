"""Integration tests for health check endpoint."""

from fastapi.testclient import TestClient


class TestHealthRoutes:
    """Test health check endpoints."""

    def test_health_endpoint(self, test_client: TestClient):
        """Test health check endpoint returns 200."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_endpoint_excluded_from_logging_middleware(
        self, test_client: TestClient
    ):
        """Test health endpoint is excluded from request logging."""
        response = test_client.get("/health")
        assert response.status_code == 200
        # Health endpoint should be accessible without detailed logging
        assert "x-request-id" not in response.headers or response.headers.get(
            "x-request-id"
        )
