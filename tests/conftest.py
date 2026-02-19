"""Pytest configuration and fixtures for auth service tests."""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings, settings
from app.core.database import Base, get_db


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with override values."""
    return Settings(
        SECRET_KEY="test-secret-key-for-testing-only",
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
        REFRESH_TOKEN_EXPIRE_DAYS=30,
        ALGORITHM="HS256",
        PROJECT_NAME="Auth Service Test",
        DEBUG=True,
        SQLITE_DATABASE_URL="sqlite+aiosqlite:///./test_auth_service.db",
        DATABASE_URL=None,
        POSTGRES_SERVER=None,
        POSTGRES_USER=None,
        POSTGRES_PASSWORD=None,
        POSTGRES_DB=None,
        LOG_LEVEL="DEBUG",
        LOG_FORMAT="json",
        RATE_LIMIT_ENABLED=False,
        CIRCUIT_BREAKER_FAILURE_THRESHOLD=3,
        CIRCUIT_BREAKER_RECOVERY_TIMEOUT=30,
        REDIS_URL=None,
        USERS_OPEN_REGISTRATION=True,
        PASSWORD_MIN_LENGTH=8,
        PASSWORD_REQUIRE_SPECIAL=True,
        PASSWORD_REQUIRE_DIGIT=True,
        PASSWORD_REQUIRE_UPPERCASE=True,
        PASSWORD_REQUIRE_LOWERCASE=True,
    )


@pytest.fixture
def test_settings_with_postgres(test_settings: Settings) -> Settings:
    """Create test settings with PostgreSQL configuration."""
    test_settings.POSTGRES_SERVER = "localhost"
    test_settings.POSTGRES_USER = "test_user"
    test_settings.POSTGRES_PASSWORD = "test_password"
    test_settings.POSTGRES_DB = "test_auth_service"
    test_settings.DATABASE_URL = None  # Will be built from components
    return test_settings


@pytest.fixture
def temp_sqlite_db() -> Generator[str, None, None]:
    """Create a temporary SQLite database file for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    try:
        os.close(db_fd)
        yield f"sqlite+aiosqlite:///{db_path}"
    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest_asyncio.fixture
async def test_db_engine(temp_sqlite_db: str):
    """Create test database engine."""
    engine = create_async_engine(
        temp_sqlite_db,
        echo=True,
        connect_args={"check_same_thread": False}
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session for testing."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


@pytest.fixture
def mock_redis():
    """Create a mock Redis client for testing."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def override_settings(test_settings: Settings, monkeypatch):
    """Override application settings for testing."""
    # Patch the settings module
    monkeypatch.setattr("app.core.config.settings", test_settings)
    monkeypatch.setattr("app.core.database.settings", test_settings)
    monkeypatch.setattr("app.core.logging.settings", test_settings)
    monkeypatch.setattr("app.core.exceptions.settings", test_settings)
    return test_settings


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.debug = MagicMock()
    return mock_logger


@pytest.fixture
def mock_correlation_id(monkeypatch):
    """Mock correlation ID context variable."""
    test_correlation_id = "test-correlation-id-12345"

    class MockContextVar:
        def __init__(self, name, default=None):
            self.name = name
            self.default = default
            self._value = default

        def get(self, default=None):
            return self._value or default or self.default

        def set(self, value):
            self._value = value

    mock_correlation_id_var = MockContextVar("correlation_id", "")
    mock_correlation_id_var.set(test_correlation_id)

    monkeypatch.setattr("app.core.logging.correlation_id", mock_correlation_id_var)
    return test_correlation_id


class AsyncContextManager:
    """Helper class for async context manager testing."""

    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context_manager():
    """Factory for creating async context managers in tests."""
    return AsyncContextManager


# Common test data
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def sample_login_data():
    """Sample login data for testing."""
    return {
        "username": "testuser",
        "password": "TestPassword123!",
    }


@pytest.fixture
def invalid_user_data():
    """Invalid user data for testing validation."""
    return {
        "email": "invalid-email",
        "username": "",
        "password": "weak",
        "first_name": "",
        "last_name": "",
    }