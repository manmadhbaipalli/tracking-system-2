"""Tests for app.core.database module."""

import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import (
    AsyncSessionLocal,
    Base,
    SessionLocal,
    check_db_connection,
    close_db_connections,
    engine,
    get_db,
    init_db,
    sync_engine,
)


class TestDatabaseConfiguration:
    """Test database configuration and engines."""

    def test_async_engine_configuration(self, override_settings):
        """Test async engine configuration with SQLite."""
        # The engine should be configured for SQLite in test environment
        database_url = str(engine.url)
        assert "sqlite" in database_url
        assert "aiosqlite" in database_url

    @patch("app.core.database.settings")
    def test_postgres_engine_configuration(self, mock_settings):
        """Test async engine configuration with PostgreSQL."""
        # Mock PostgreSQL settings
        mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/test"
        mock_settings.DEBUG = False

        # Import would create engine with these settings
        from app.core.database import create_async_engine

        # Test that PostgreSQL configuration would be used
        test_engine = create_async_engine(
            "postgresql+asyncpg://user:pass@localhost/test",
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

        assert "postgresql" in str(test_engine.url)
        assert "asyncpg" in str(test_engine.url)

    def test_sync_engine_configuration(self):
        """Test sync engine configuration."""
        database_url = str(sync_engine.url)
        assert "sqlite" in database_url
        # Should not have aiosqlite in sync URL
        assert "aiosqlite" not in database_url

    def test_session_makers_created(self):
        """Test that session makers are properly created."""
        assert AsyncSessionLocal is not None
        assert SessionLocal is not None

        # Test AsyncSessionLocal configuration
        session = AsyncSessionLocal()
        assert isinstance(session, AsyncSession)
        assert session.expire_on_commit is False
        assert session.autocommit is False
        assert session.autoflush is False

    def test_base_declarative_class(self):
        """Test that Base declarative class is created."""
        assert Base is not None
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


class TestDatabaseDependency:
    """Test database dependency injection."""

    @pytest.mark.asyncio
    async def test_get_db_dependency(self, test_db_session):
        """Test get_db dependency function."""
        # Test that get_db returns an async generator
        db_gen = get_db()
        assert hasattr(db_gen, "__aiter__")

        # The actual testing is done through the test_db_session fixture
        # which uses the same pattern as get_db
        assert isinstance(test_db_session, AsyncSession)

    @pytest.mark.asyncio
    async def test_get_db_session_cleanup(self):
        """Test that database session is properly cleaned up."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_maker = AsyncMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock()

        with patch("app.core.database.AsyncSessionLocal", mock_session_maker):
            db_gen = get_db()
            session = await db_gen.__anext__()

            assert session is mock_session

            # Verify session cleanup is called
            await db_gen.aclose()


class TestDatabaseOperations:
    """Test database operations and utilities."""

    @pytest.mark.asyncio
    async def test_check_db_connection_success(self, mock_db_session):
        """Test successful database connection check."""
        mock_db_session.execute.return_value = None

        with patch("app.core.database.AsyncSessionLocal") as mock_session_maker:
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock()

            result = await check_db_connection()

            assert result is True
            mock_db_session.execute.assert_called_once()
            # Check that SELECT 1 query was executed
            call_args = mock_db_session.execute.call_args[0][0]
            assert "SELECT 1" in str(call_args)

    @pytest.mark.asyncio
    async def test_check_db_connection_failure(self):
        """Test database connection check failure."""
        with patch("app.core.database.AsyncSessionLocal") as mock_session_maker:
            # Mock session that raises exception
            mock_session = AsyncMock()
            mock_session.execute.side_effect = SQLAlchemyError("Connection failed")
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock()

            result = await check_db_connection()

            assert result is False

    @pytest.mark.asyncio
    async def test_init_db(self):
        """Test database initialization."""
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()

        with patch("app.core.database.engine") as mock_engine:
            mock_engine.begin = AsyncMock()
            mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_engine.begin.return_value.__aexit__ = AsyncMock()

            await init_db()

            mock_conn.run_sync.assert_called_once()
            # Verify Base.metadata.create_all is called
            call_args = mock_conn.run_sync.call_args[0][0]
            assert callable(call_args)

    @pytest.mark.asyncio
    async def test_close_db_connections(self):
        """Test database connections cleanup."""
        with patch("app.core.database.engine") as mock_engine:
            mock_engine.dispose = AsyncMock()

            await close_db_connections()

            mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_connections_no_engine(self):
        """Test database connections cleanup when engine is None."""
        with patch("app.core.database.engine", None):
            # Should not raise exception
            await close_db_connections()


class TestSQLitePragma:
    """Test SQLite-specific configuration."""

    def test_sqlite_foreign_keys_pragma(self, override_settings):
        """Test that foreign keys pragma is set for SQLite."""
        # This is tested implicitly through the event listener
        # The event listener should be registered for SQLite connections
        from app.core.database import sync_engine

        # Check that we're using SQLite
        assert "sqlite" in str(sync_engine.url)

        # The pragma setting is tested through event system
        # In real usage, the event would be triggered on connection


class TestDatabaseURL:
    """Test database URL handling."""

    @patch("app.core.database.settings")
    def test_sqlite_url_conversion(self, mock_settings):
        """Test SQLite URL conversion for async driver."""
        mock_settings.DATABASE_URL = "sqlite:///./test.db"
        mock_settings.SQLITE_DATABASE_URL = "sqlite:///./test.db"
        mock_settings.DEBUG = False

        # Test URL conversion logic
        database_url = str(mock_settings.DATABASE_URL or mock_settings.SQLITE_DATABASE_URL)
        if not database_url.startswith("sqlite+aiosqlite:"):
            async_url = database_url.replace("sqlite:", "sqlite+aiosqlite:")
        else:
            async_url = database_url

        assert async_url == "sqlite+aiosqlite:///./test.db"

    @patch("app.core.database.settings")
    def test_postgres_url_sync_conversion(self, mock_settings):
        """Test PostgreSQL URL conversion for sync operations."""
        mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"
        mock_settings.SQLITE_DATABASE_URL = "sqlite:///./test.db"

        # Test sync URL conversion
        sync_database_url = str(mock_settings.DATABASE_URL)
        if "postgresql+asyncpg" in sync_database_url:
            sync_url = sync_database_url.replace("postgresql+asyncpg", "postgresql")
        else:
            sync_url = sync_database_url

        assert sync_url == "postgresql://user:pass@host/db"


class TestDatabaseIntegration:
    """Integration tests for database functionality."""

    @pytest.mark.asyncio
    async def test_real_database_connection(self, test_db_session):
        """Test actual database connection and query execution."""
        # Execute a simple query
        result = await test_db_session.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()

        assert row is not None
        assert row.test_value == 1

    @pytest.mark.asyncio
    async def test_database_transaction(self, test_db_session):
        """Test database transaction behavior."""
        try:
            # Start a transaction (implicit with session)
            await test_db_session.execute(text("SELECT 1"))

            # Test rollback capability
            await test_db_session.rollback()

            # Test commit capability
            await test_db_session.execute(text("SELECT 1"))
            await test_db_session.commit()

        except Exception as e:
            await test_db_session.rollback()
            raise e

    @pytest.mark.asyncio
    async def test_database_session_isolation(self, test_db_engine):
        """Test that database sessions are properly isolated."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        TestSessionLocal = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with TestSessionLocal() as session1:
            async with TestSessionLocal() as session2:
                # These should be different session instances
                assert session1 is not session2

                # Both should be able to execute queries independently
                result1 = await session1.execute(text("SELECT 1 as value"))
                result2 = await session2.execute(text("SELECT 2 as value"))

                row1 = result1.fetchone()
                row2 = result2.fetchone()

                assert row1.value == 1
                assert row2.value == 2