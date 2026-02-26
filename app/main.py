import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.exception_handlers import app_exception_handler, validation_exception_handler, generic_exception_handler
from app.exceptions import AppException
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers import auth, users, health


def _configure_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    if settings.app_env == "production":
        try:
            from pythonjsonlogger import jsonlogger
            handler = logging.StreamHandler()
            formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            logging.basicConfig(level=log_level, handlers=[handler])
        except ImportError:
            logging.basicConfig(level=log_level)
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="FastAPI Auth & Circuit Breaker App",
    version="1.0.0",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    lifespan=lifespan,
)

# Middleware (registered in reverse order — last added = outermost)
app.add_middleware(LoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(health.router)
