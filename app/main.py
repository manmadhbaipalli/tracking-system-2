"""FastAPI application instance and startup configuration."""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import create_tables
from app.api.v1 import api_router
from app.core.logging import (
    setup_logging,
    get_logger,
    set_correlation_id,
    log_request_info,
    log_response_info,
)
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    integrity_error_handler,
    general_exception_handler,
)

# Setup logging
setup_logging()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Auth Serve application")

    # Create database tables
    try:
        await create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise

    logger.info("Auth Serve application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Auth Serve application")


# Create FastAPI application
app = FastAPI(
    title="Auth Serve",
    description="A FastAPI-based authentication service with user registration, login, and JWT token management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Request/Response logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware to log requests and responses with correlation IDs."""
    # Set correlation ID for request tracing
    correlation_id = set_correlation_id()

    # Log request
    start_time = time.time()
    log_request_info(
        method=request.method,
        url=request.url,
        headers=dict(request.headers),
        correlation_id=correlation_id,
    )

    # Process request
    try:
        response: Response = await call_next(request)

        # Log response
        processing_time = time.time() - start_time
        log_response_info(
            status_code=response.status_code,
            processing_time=processing_time,
            correlation_id=correlation_id,
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response

    except Exception as e:
        # Log exception
        processing_time = time.time() - start_time
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "processing_time": processing_time,
                "correlation_id": correlation_id,
            },
            exc_info=True
        )
        raise


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-serve",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information."""
    return {
        "message": "Welcome to Auth Serve",
        "description": "A FastAPI-based authentication service",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health"
    }