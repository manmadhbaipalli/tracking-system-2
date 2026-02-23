"""
Test the main application functionality.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.async_test
async def test_app_creation():
    """Test that the app can be created successfully."""
    from app.main import create_app

    app = create_app()
    assert app is not None
    assert app.title == "Insurance Management System"


@pytest_asyncio.async_test
async def test_health_check(test_client: AsyncClient):
    """Test the health check endpoint."""
    response = await test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest_asyncio.async_test
async def test_openapi_docs(test_client: AsyncClient):
    """Test that OpenAPI docs are available."""
    response = await test_client.get("/docs")
    assert response.status_code == 200


@pytest_asyncio.async_test
async def test_openapi_json(test_client: AsyncClient):
    """Test that OpenAPI JSON schema is available."""
    response = await test_client.get("/openapi.json")
    assert response.status_code == 200

    data = response.json()
    assert data["info"]["title"] == "Insurance Management System"
    assert "paths" in data