from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

Base = declarative_base()

engine_kwargs = {
    "echo": settings.ENVIRONMENT == "development",
}

# Only add pool_size for PostgreSQL
if "postgresql" in settings.DATABASE_URL:
    engine_kwargs["pool_size"] = settings.DATABASE_MAX_POOL_SIZE

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide async database session to routes."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Initialize database and create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
