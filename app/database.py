from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

Base = declarative_base()

# Lazy initialization of engine and session factory
_engine = None
_AsyncSessionLocal = None


def get_engine():
    """Get or create the async engine."""
    global _engine
    if _engine is None:
        engine_kwargs = {
            "echo": settings.ENVIRONMENT == "development",
        }
        # Only add pool_size for PostgreSQL
        if "postgresql" in settings.DATABASE_URL:
            engine_kwargs["pool_size"] = settings.DATABASE_MAX_POOL_SIZE
        _engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
    return _engine


def get_async_session_local():
    """Get or create the async session factory."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _AsyncSessionLocal


# Create a lazy-loading proxy for backward compatibility
class EngineProxy:
    """Proxy object that defers engine creation until first use."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)


engine = EngineProxy()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide async database session to routes."""
    session_factory = get_async_session_local()
    async with session_factory() as session:
        yield session


async def init_db() -> None:
    """Initialize database and create all tables."""
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
