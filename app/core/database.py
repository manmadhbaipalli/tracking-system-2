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
from sqlalchemy import String, DateTime
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


# Create async engine with conditional pooling parameters
engine_kwargs = {
    "echo": settings.database.echo,
    "pool_pre_ping": True,  # Validate connections before use
}

# Only add pooling parameters for PostgreSQL (not SQLite)
if settings.database_url.startswith(("postgresql", "postgres")):
    engine_kwargs.update({
        "pool_size": settings.database.pool_size,
        "max_overflow": settings.database.max_overflow,
    })

engine = create_async_engine(settings.database_url, **engine_kwargs)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for FastAPI routes.

    Provides an async database session with proper cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize the database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Close the database engine."""
    await engine.dispose()