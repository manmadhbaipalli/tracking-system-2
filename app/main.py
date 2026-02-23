"""FastAPI application setup with middleware, exception handlers, and route registration."""

import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import auth_router, users_router
from app.config import settings
from app.core.circuit_breaker import get_all_circuit_breaker_states
from app.core.exceptions import AuthServiceException, CircuitBreakerError
from app.database import create_tables, close_db
from app.utils.logging import get_logger, log_context, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with correlation IDs."""

    async def dispatch(self, request: Request, call_next):
        """Process request with logging and correlation ID."""
        correlation_id = str(uuid.uuid4())[:8]

        with log_context(correlation_id=correlation_id):
            # Log request
            logger.info(
                "Request started",
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params),
                client_ip=request.client.host if request.client else None,
            )

            try:
                response = await call_next(request)

                # Log response
                logger.info(
                    "Request completed",
                    status_code=response.status_code,
                    method=request.method,
                    path=request.url.path,
                )

                # Add correlation ID to response headers
                response.headers["X-Correlation-ID"] = correlation_id
                return response

            except Exception as e:
                logger.error(
                    "Request failed",
                    method=request.method,
                    path=request.url.path,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown tasks."""
    # Startup
    logger.info("Starting up Auth-Serve application")
    try:
        await create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Auth-Serve application")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Failed to close database connections", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="FastAPI Authentication Service with JWT tokens, circuit breakers, and comprehensive logging",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)


@app.exception_handler(AuthServiceException)
async def auth_service_exception_handler(request: Request, exc: AuthServiceException) -> JSONResponse:
    """Handle custom auth service exceptions."""
    logger.warning(
        "Auth service exception",
        error_code=exc.error_code,
        error_message=exc.message,
        path=request.url.path,
    )

    status_code_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "USER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "USER_ALREADY_EXISTS": status.HTTP_409_CONFLICT,
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "CIRCUIT_BREAKER_OPEN": status.HTTP_503_SERVICE_UNAVAILABLE,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "TOKEN_ERROR": status.HTTP_401_UNAUTHORIZED,
    }

    status_code = status_code_map.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "path": request.url.path,
        },
    )


@app.exception_handler(CircuitBreakerError)
async def circuit_breaker_exception_handler(request: Request, exc: CircuitBreakerError) -> JSONResponse:
    """Handle circuit breaker exceptions."""
    logger.warning(
        "Circuit breaker exception",
        error_message=exc.message,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "SERVICE_UNAVAILABLE",
            "message": exc.message,
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(
        "Request validation error",
        errors=exc.errors(),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred",
            "path": request.url.path,
        },
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    Application health check endpoint.

    Returns:
        Dict[str, Any]: Health status and system information
    """
    circuit_breaker_states = await get_all_circuit_breaker_states()

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
        "circuit_breakers": circuit_breaker_states,
    }


# Root endpoint
@app.get("/", tags=["root"])
async def read_root() -> Dict[str, str]:
    """
    Root endpoint providing basic API information.

    Returns:
        Dict[str, str]: API welcome message and documentation links
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "documentation": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health",
    }


# Include routers
app.include_router(auth_router)
app.include_router(users_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )