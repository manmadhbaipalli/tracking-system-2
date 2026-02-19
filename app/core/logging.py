"""Centralized logging configuration with structured output."""

import json
import logging
import logging.config
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

# Context variable to store correlation ID
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the log record."""
        record.correlation_id = correlation_id.get("")
        return True


class JSONFormatter(logging.Formatter):
    """JSON log formatter with structured output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        correlation_id_value = getattr(record, "correlation_id", "")
        if correlation_id_value:
            log_data["correlation_id"] = correlation_id_value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "correlation_id"
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    """Setup application logging configuration."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Choose formatter based on configuration
    if settings.LOG_FORMAT.lower() == "json":
        formatter_class = "app.core.logging.JSONFormatter"
        format_string = ""  # Not used for JSON formatter
    else:
        formatter_class = "logging.Formatter"
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(correlation_id)s - %(message)s"
        )

    # Configure handlers
    handlers = ["console"]
    console_handler = {
        "class": "logging.StreamHandler",
        "stream": sys.stdout,
        "formatter": "default",
        "filters": ["correlation_id"],
    }

    handler_config = {
        "console": console_handler,
    }

    # Add file handler if configured
    if settings.LOG_FILE:
        handlers.append("file")
        handler_config["file"] = {
            "class": "logging.FileHandler",
            "filename": settings.LOG_FILE,
            "formatter": "default",
            "filters": ["correlation_id"],
        }

    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": "app.core.logging.CorrelationIDFilter",
            },
        },
        "formatters": {
            "default": {
                "()": formatter_class,
                "format": format_string,
            },
        },
        "handlers": handler_config,
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": handlers,
                "propagate": False,
            },
            "sqlalchemy": {
                "level": logging.WARNING,
                "handlers": handlers,
                "propagate": False,
            },
            "uvicorn": {
                "level": logging.INFO,
                "handlers": handlers,
                "propagate": False,
            },
            "fastapi": {
                "level": logging.INFO,
                "handlers": handlers,
                "propagate": False,
            },
        },
        "root": {
            "level": logging.WARNING,
            "handlers": handlers,
        },
    }

    # Apply logging configuration
    logging.config.dictConfig(logging_config)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response details."""
        # Generate correlation ID
        request_correlation_id = str(uuid.uuid4())
        correlation_id.set(request_correlation_id)

        # Add correlation ID to request headers
        request.headers.__dict__["_list"].append(
            (b"x-correlation-id", request_correlation_id.encode())
        )

        # Log request
        logger = logging.getLogger("app.middleware")
        start_time = time.time()

        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "content_length": request.headers.get("content-length"),
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "response_size": response.headers.get("content-length"),
                }
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = request_correlation_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            raise


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with proper configuration."""
    return logging.getLogger(f"app.{name}")


# Initialize logging on import
setup_logging()