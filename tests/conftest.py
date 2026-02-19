"""Pytest fixtures and configuration for testing."""

import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import timedelta

from app.main import app
from app.database import Base
from app.config import settings
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.password import hash_password
from app.models.user import User
from fastapi.testclient import TestClient


# Override database URL for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Global test engine and session factory
_test_engine = None
_TestAsyncSession = None


def pytest_configure(config):
    """Create test database on pytest startup."""
    global _test_engine, _TestAsyncSession
    import asyncio

    async def setup():
        global _test_engine, _TestAsyncSession
        _test_engine = create_async_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _TestAsyncSession = async_sessionmaker(
            _test_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    asyncio.run(setup())


def pytest_unconfigure(config):
    """Cleanup test database on pytest shutdown."""
    global _test_engine
    import asyncio

    async def cleanup():
        global _test_engine
        if _test_engine:
            async with _test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await _test_engine.dispose()

    asyncio.run(cleanup())


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_session():
    """Create test database session."""
    global _TestAsyncSession
    async with _TestAsyncSession() as session:
        yield session


@pytest.fixture
def test_client():
    """Create test client for FastAPI."""
    from app import dependencies
    global _TestAsyncSession

    async def override_get_db_session():
        async with _TestAsyncSession() as session:
            yield session

    app.dependency_overrides[dependencies.get_db_session] = override_get_db_session

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db_session: AsyncSession):
    """Create a test user in the database."""
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_tokens(test_user: User):
    """Create tokens for test user."""
    return {
        "access_token": create_access_token(test_user.id),
        "refresh_token": create_refresh_token(test_user.id),
    }


@pytest.fixture
async def expired_access_token(test_user: User):
    """Create an expired access token."""
    return create_access_token(
        test_user.id,
        expires_delta=timedelta(minutes=-1)
    )


@pytest.fixture
def test_user_data():
    """Test user registration data."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword123",
    }


@pytest.fixture
def invalid_user_data():
    """Invalid user data with short password."""
    return {
        "username": "shortpass",
        "email": "short@example.com",
        "password": "short",
    }
