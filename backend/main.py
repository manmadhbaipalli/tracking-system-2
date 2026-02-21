"""
Claims Service Platform - FastAPI Application Entry Point

Main application setup with CORS middleware, API routes, and error handling.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, policies, claims, payments
from app.services.audit_service import AuditService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    logger.info("Starting Claims Service Platform...")

    # Create database tables
    Base.metadata.create_all(bind=engine)

    yield

    # Shutdown
    logger.info("Shutting down Claims Service Platform...")


app = FastAPI(
    title="Claims Service Platform API",
    description="Integrated Policy, Claims, and Payments Management Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID for tracing"""
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    """Audit logging middleware for all requests"""
    start_time = time.time()

    # Store request info
    request.state.start_time = start_time
    request.state.client_ip = request.client.host
    request.state.user_agent = request.headers.get("user-agent", "")

    response = await call_next(request)

    # Log request completion
    process_time = time.time() - start_time
    logger.info(
        f"Request {request.state.request_id} - "
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "claims-service-platform"}


# API Routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(claims.router, prefix="/api/claims", tags=["Claims"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )