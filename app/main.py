"""FastAPI application initialization."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.db import Base, engine
from app.utils.logging import setup_logging, get_logger
from app.middleware.logging import logging_middleware
from app.middleware.exception import exception_middleware
from app.auth.router import router as auth_router

logger = get_logger(__name__)

setup_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Application",
    description="A production-ready FastAPI app with auth, logging, and circuit breaker",
    version="1.0.0",
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware wrapper."""

    async def dispatch(self, request: Request, call_next):
        return await logging_middleware(request, call_next)


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Exception middleware wrapper."""

    async def dispatch(self, request: Request, call_next):
        return await exception_middleware(request, call_next)


app.add_middleware(ExceptionMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(auth_router)


@app.get("/")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Status message
    """
    return {"status": "ok"}
