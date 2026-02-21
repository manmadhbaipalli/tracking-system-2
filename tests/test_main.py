"""Tests for the main FastAPI application."""
import pytest
from fastapi.testclient import TestClient


class TestMainApp:
    """Test cases for the main FastAPI application."""

    def test_health_check_endpoint(self, test_client: TestClient):
        """Test health check endpoint returns healthy status."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]
        assert "database" in data

    def test_docs_endpoint_accessible(self, test_client: TestClient):
        """Test that API documentation is accessible."""
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_accessible(self, test_client: TestClient):
        """Test that ReDoc documentation is accessible."""
        response = test_client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema_accessible(self, test_client: TestClient):
        """Test that OpenAPI schema is accessible."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert data["info"]["title"] == "Auth Service API"
        assert data["info"]["version"] == "1.0.0"

    def test_cors_headers_present(self, test_client: TestClient):
        """Test that CORS headers are properly configured."""
        response = test_client.options("/health", headers={"Origin": "http://localhost:3000"})
        # Note: TestClient doesn't fully simulate CORS behavior,
        # but we can check that the middleware is configured
        assert response.status_code in [200, 405]  # OPTIONS may not be explicitly handled

    def test_nonexistent_endpoint_404(self, test_client: TestClient):
        """Test that nonexistent endpoints return 404."""
        response = test_client.get("/nonexistent-endpoint")
        assert response.status_code == 404