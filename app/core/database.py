"""SQLAlchemy database configuration and session management."""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create async engine
if settings.DATABASE_URL and "postgresql" in str(settings.DATABASE_URL):
    # PostgreSQL with asyncpg
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
else:
    # SQLite with aiosqlite
    database_url = str(settings.DATABASE_URL or settings.SQLITE_DATABASE_URL)
    if not database_url.startswith("sqlite+aiosqlite:"):
        database_url = database_url.replace("sqlite:", "sqlite+aiosqlite:")

    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Create sync engine for Alembic migrations
sync_database_url = str(settings.DATABASE_URL or settings.SQLITE_DATABASE_URL)
if "postgresql+asyncpg" in sync_database_url:
    sync_database_url = sync_database_url.replace("postgresql+asyncpg", "postgresql")
elif "sqlite+aiosqlite" in sync_database_url:
    sync_database_url = sync_database_url.replace("sqlite+aiosqlite", "sqlite")

sync_engine = create_engine(
    sync_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True if "postgresql" in sync_database_url else False,
)

# Create sync session for migrations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Create declarative base
Base = declarative_base()


# Enable foreign keys for SQLite
if "sqlite" in str(settings.DATABASE_URL or settings.SQLITE_DATABASE_URL):
    @event.listens_for(sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable foreign keys for SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


async def get_db() -> AsyncSession:
    """Get database session dependency for FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base
        from app.models import user  # noqa: F401

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def close_db_connections() -> None:
    """Close database connections gracefully."""
    if engine:
        await engine.dispose()