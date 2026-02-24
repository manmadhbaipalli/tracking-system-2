"""FastAPI application entry point with middleware, CORS, and route registration."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_database, close_database
from app.api.v1 import api_router
from app.utils.exceptions import (
    validation_error_handler, not_found_error_handler, authentication_error_handler,
    authorization_error_handler, business_logic_error_handler, payment_error_handler,
    external_service_error_handler, general_exception_handler,
    ValidationError, NotFoundError, AuthenticationError, AuthorizationError,
    BusinessLogicError, PaymentError, ExternalServiceError
)
from app.utils.correlation import CorrelationIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_database()
    yield
    # Shutdown
    await close_database()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Integrated Policy, Claims, and Payments Platform",
        lifespan=lifespan
    )

    # Add custom middleware
    app.add_middleware(CorrelationIDMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(AuthorizationError, authorization_error_handler)
    app.add_exception_handler(BusinessLogicError, business_logic_error_handler)
    app.add_exception_handler(PaymentError, payment_error_handler)
    app.add_exception_handler(ExternalServiceError, external_service_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include API routes
    app.include_router(api_router)

    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}

    return app


app = create_app()