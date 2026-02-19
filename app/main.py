"""FastAPI application entry point with middleware and route registration."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, init_db
from app.middleware.logging import LoggingMiddleware
from app.middleware.exception import exception_handler
from app.utils.exceptions import AppException
from app.utils.logger import setup_logging
from app.routes import auth, health

# Initialize logging
setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app startup and shutdown."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Authentication Service",
    description="FastAPI service with authentication, logging, and exception handling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Register middleware (order matters!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handler
app.add_exception_handler(AppException, exception_handler)
app.add_exception_handler(Exception, exception_handler)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
