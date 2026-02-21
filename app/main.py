"""FastAPI application entry point with middleware and route setup."""
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import auth, users
from app.core.config import settings
from app.core.exceptions import (
    AuthServiceException,
    auth_service_exception_handler,
    general_exception_handler,
    http_exception_handler,
)
from app.core.logging import CorrelationMiddleware, setup_logging
from app.db.session import engine
from app.models.user import Base

# Set up logging first
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Auth Service API",
    description="FastAPI Authentication Service with JWT tokens",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware
app.add_middleware(CorrelationMiddleware)

# Add exception handlers
app.add_exception_handler(AuthServiceException, auth_service_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connectivity
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "database": "disconnected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy"}


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Auth Service API")

    # Create database tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Auth Service API")
    await engine.dispose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )