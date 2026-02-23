"""
Test configuration and fixtures for the insurance management system.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from app.core.database import Base, get_database_session
from app.core.config import Settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_app(test_db):
    """Create test FastAPI app."""
    app = create_app()

    # Override database dependency
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_database_session] = override_get_db

    return app


@pytest_asyncio.fixture
async def test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        environment="testing",
        debug=True,
        jwt_secret_key="test-jwt-secret-key-for-unit-testing-minimum-32-chars-long!",
        database={"sqlite_url": TEST_DATABASE_URL}
    )