"""
Database configuration and session management using async SQLAlchemy.

Provides:
- Async database engine and session factory
- Base model class with common fields
- Database dependency for FastAPI routes
- Connection pooling and lifecycle management
"""

import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional
from sqlalchemy import String, DateTime, pool, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.types import TypeDecorator, CHAR

from app.core.config import settings


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36).
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class Base(DeclarativeBase):
    """Base model class with common fields and utilities."""

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Engine and session factory - lazily initialized
_engine = None
_AsyncSessionLocal = None


def _get_engine():
    """Get or create the async database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        engine_kwargs = {
            "echo": settings.database.echo,
            "pool_pre_ping": True,  # Validate connections before use
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "connect_args": {"check_same_thread": False} if "sqlite" in settings.database_url else {},
        }

        # Add pooling parameters for PostgreSQL (not SQLite)
        if settings.database_url.startswith(("postgresql", "postgres")):
            engine_kwargs.update({
                "pool_size": settings.database.pool_size,
                "max_overflow": settings.database.max_overflow,
                "pool_timeout": 30,  # Timeout for getting connection from pool
            })
        elif "sqlite" in settings.database_url:
            # SQLite specific optimizations
            engine_kwargs.update({
                "poolclass": pool.StaticPool,  # Use static pool for SQLite
            })

        _engine = create_async_engine(settings.database_url, **engine_kwargs)
    return _engine


def _get_session_factory():
    """Get or create the async session factory (lazy initialization)."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,  # Manual flush control for better performance
            autocommit=False
        )
    return _AsyncSessionLocal




async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for FastAPI routes.

    Provides an async database session with proper cleanup.
    """
    async with _get_session_factory()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Legacy alias for compatibility
get_db = get_database_session


async def init_database() -> None:
    """Initialize the database by creating all tables."""
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Close the database engine."""
    if _engine is not None:
        await _engine.dispose()


async def check_database_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        async with _get_engine().begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def get_database_session_context():
    """Context manager for database sessions with automatic transaction handling."""
    async with _get_session_factory()() as session:
        try:
            async with session.begin():
                yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseSessionManager:
    """Enhanced database session manager for complex operations."""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        """Enter async context and create session."""
        self.session = _get_session_factory()()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context with proper cleanup."""
        if self.session:
            if exc_type is not None:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()
            self.session = None

    async def commit(self):
        """Commit current transaction."""
        if self.session:
            await self.session.commit()

    async def rollback(self):
        """Rollback current transaction."""
        if self.session:
            await self.session.rollback()

    async def flush(self):
        """Flush changes to database without committing."""
        if self.session:
            await self.session.flush()