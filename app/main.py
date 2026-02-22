"""Main FastAPI application entry point."""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.exceptions import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.api.v1 import api_router
from app.database import create_tables
from fastapi.exceptions import HTTPException, RequestValidationError

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up FastAPI application")

    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise

    logger.info("FastAPI application startup completed")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()

    # Log request
    logger.info(
        "HTTP request started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
        },
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response
    logger.info(
        "HTTP request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
        },
    )

    return response


# Register exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to FastAPI Application",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


# Health check endpoint at root level
@app.get("/health", tags=["health"])
async def health_check():
    """Application health check."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
    }


if __name__ == "__main__":
    import uvicorn
    import time

    logger.info("Starting FastAPI development server")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )