"""Database configuration and session management"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

from .config import settings

# Create declarative base for models
Base = declarative_base()

# Configure async engine
if settings.database_url.startswith("sqlite"):
    # SQLite configuration with async support
    database_url = settings.database_url.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(
        database_url,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=settings.debug,
    )
else:
    # PostgreSQL configuration
    database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.debug,
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session for FastAPI routes.

    Yields:
        AsyncSession: Database session instance
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all database tables (for testing)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)