"""Integration tests for Swagger and API documentation."""

from fastapi.testclient import TestClient


class TestSwaggerDocs:
    """Test Swagger and documentation endpoints."""

    def test_swagger_ui_available(self, test_client: TestClient):
        """Test Swagger UI is available at /docs."""
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_openapi_schema_available(self, test_client: TestClient):
        """Test OpenAPI schema is available."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "components" in data

    def test_openapi_schema_has_auth_endpoints(self, test_client: TestClient):
        """Test OpenAPI schema includes auth endpoints."""
        response = test_client.get("/openapi.json")
        data = response.json()
        paths = data["paths"]
        assert "/auth/register" in paths
        assert "/auth/login" in paths
        assert "/auth/refresh" in paths

    def test_openapi_schema_has_health_endpoint(self, test_client: TestClient):
        """Test OpenAPI schema includes health endpoint."""
        response = test_client.get("/openapi.json")
        data = response.json()
        paths = data["paths"]
        assert "/health" in paths

    def test_redoc_available(self, test_client: TestClient):
        """Test ReDoc is available at /redoc."""
        response = test_client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_has_tags(self, test_client: TestClient):
        """Test OpenAPI schema includes tags for organization."""
        response = test_client.get("/openapi.json")
        data = response.json()
        assert "tags" in data
        tags = [tag["name"] for tag in data["tags"]]
        assert "authentication" in tags
        assert "health" in tags

    def test_endpoints_have_descriptions(self, test_client: TestClient):
        """Test that endpoints have descriptions for documentation."""
        response = test_client.get("/openapi.json")
        data = response.json()
        paths = data["paths"]

        # Check register endpoint
        assert "post" in paths["/auth/register"]
        assert "description" in paths["/auth/register"]["post"]

        # Check login endpoint
        assert "post" in paths["/auth/login"]
        assert "description" in paths["/auth/login"]["post"]

    def test_app_info_in_openapi(self, test_client: TestClient):
        """Test that app info is in OpenAPI schema."""
        response = test_client.get("/openapi.json")
        data = response.json()
        info = data["info"]
        assert "title" in info
        assert "version" in info
        assert info["title"] == "Authentication Service"
