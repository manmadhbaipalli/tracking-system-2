"""FastAPI Auth Service - Main Application Entry Point"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import create_tables
from .core.logging import (
    configure_logging,
    CorrelationIDMiddleware,
    LoggingMiddleware
)
from .core.exceptions import (
    AuthServiceException,
    auth_service_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from .api.auth import router as auth_router
from .api.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting FastAPI Auth Service...")

    try:
        # Create database tables
        await create_tables()
        logger.info("Database tables created successfully")

        # Application is ready
        logger.info("FastAPI Auth Service started successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    finally:
        # Shutdown
        logger.info("FastAPI Auth Service shutting down...")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    # Configure logging first
    configure_logging()
    logger = logging.getLogger(__name__)

    # Create FastAPI application
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-ready FastAPI authentication service with JWT tokens, user management, and comprehensive logging",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Register exception handlers
    app.add_exception_handler(AuthServiceException, auth_service_exception_handler)
    app.add_exception_handler(HTTPException, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include API routers
    app.include_router(auth_router)
    app.include_router(users_router)

    # Health check endpoints
    @app.get(
        "/health",
        tags=["health"],
        summary="Health check",
        description="Check if the service is healthy and responsive"
    )
    async def health_check() -> Dict[str, Any]:
        """
        Health check endpoint.

        Returns:
            dict: Health status information
        """
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug
        }

    @app.get(
        "/readiness",
        tags=["health"],
        summary="Readiness check",
        description="Check if the service is ready to accept requests"
    )
    async def readiness_check() -> Dict[str, Any]:
        """
        Readiness check endpoint.

        Returns:
            dict: Readiness status information
        """
        # In a production environment, you might want to check:
        # - Database connectivity
        # - External service dependencies
        # - Cache connectivity

        return {
            "status": "ready",
            "service": settings.app_name,
            "version": settings.app_version,
            "checks": {
                "database": "ok",  # Would check actual DB connectivity
                "cache": "ok",     # Would check cache if implemented
            }
        }

    @app.get(
        "/",
        tags=["root"],
        summary="Root endpoint",
        description="Service information and documentation links"
    )
    async def root() -> Dict[str, Any]:
        """
        Root endpoint with service information.

        Returns:
            dict: Service information and links
        """
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json"
            },
            "endpoints": {
                "health": "/health",
                "readiness": "/readiness",
                "auth": "/auth",
                "users": "/users"
            }
        }

    logger.info(f"FastAPI application created: {settings.app_name} v{settings.app_version}")
    return app


# Create application instance
app = create_application()


# For debugging and development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use our custom logging configuration
        access_log=False,  # Handled by our logging middleware
    )