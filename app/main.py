import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine, async_session_maker
from app.models.base import Base
from app.exceptions import AppException, app_exception_handler
from app.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware
from app.routers.auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler"""
    # Startup: create tables (dev only — use Alembic in prod)
    if settings.environment == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    logger.info("Application started: %s", settings.app_name)
    yield

    # Shutdown
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="FastAPI Authentication API with JWT token support",
    lifespan=lifespan,
)

# Middleware (order matters — first added = outermost)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-Id"],
    expose_headers=["X-Correlation-Id"],
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)

# Routers
app.include_router(auth_router)


# Health check endpoints
@app.get("/health/live", tags=["Health"])
async def liveness():
    """Liveness probe for container orchestration"""
    return {"status": "UP"}


@app.get("/health/ready", tags=["Health"])
async def readiness():
    """
    Readiness probe - checks database connectivity.
    Returns 503 if database is unreachable.
    """
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "UP", "checks": {"database": "UP"}}
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "DOWN", "checks": {"database": "DOWN"}}
        )


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": {
            "liveness": "/health/live",
            "readiness": "/health/ready"
        }
    }
