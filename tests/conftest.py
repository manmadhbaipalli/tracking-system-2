"""Pytest configuration and fixtures for the auth service tests."""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_database_session
from app.core.config import settings
from app.db.session import Base
from app.main import app

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncSession:
    """Create test database session."""
    TestSessionLocal = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def override_get_db(test_db_session: AsyncSession):
    """Override database dependency for testing."""
    async def _get_db():
        yield test_db_session

    return _get_db


@pytest.fixture(scope="function")
def test_client(override_get_db) -> TestClient:
    """Create test client with overridden dependencies."""
    app.dependency_overrides[get_database_session] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_test_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with overridden dependencies."""
    app.dependency_overrides[get_database_session] = override_get_db
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def test_user_data_invalid():
    """Invalid test user data fixture."""
    return {
        "email": "invalid-email",
        "password": "short",
    }