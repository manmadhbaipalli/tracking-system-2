"""Centralized logging configuration."""

import json
import logging
import logging.config
import sys
import uuid
from typing import Dict, Any
from contextvars import ContextVar
from datetime import datetime

from app.config import settings

# Context variable to store correlation ID across async contexts
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_ctx.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage",
                "exc_info", "exc_text", "stack_info"
            ):
                log_data[key] = value

        return json.dumps(log_data, default=str, ensure_ascii=False)


class CorrelationFilter(logging.Filter):
    """Filter to add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to record if available."""
        correlation_id = correlation_id_ctx.get()
        if correlation_id:
            record.correlation_id = correlation_id
        return True


def setup_logging() -> None:
    """Configure application logging."""

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "filters": {
            "correlation": {
                "()": CorrelationFilter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json" if not settings.debug else "standard",
                "filters": ["correlation"],
            },
        },
        "root": {
            "level": settings.log_level.upper(),
            "handlers": ["console"],
        },
        "loggers": {
            "app": {
                "level": settings.log_level.upper(),
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "INFO" if settings.debug else "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def set_correlation_id(correlation_id: str = None) -> str:
    """Set correlation ID for request tracing."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_ctx.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id_ctx.get()


def log_request_info(method: str, url: str, **kwargs) -> None:
    """Log HTTP request information."""
    logger = get_logger("app.requests")
    logger.info(
        f"{method} {url}",
        extra={
            "request_method": method,
            "request_url": str(url),
            **kwargs
        }
    )


def log_response_info(status_code: int, processing_time: float, **kwargs) -> None:
    """Log HTTP response information."""
    logger = get_logger("app.requests")
    logger.info(
        f"Response: {status_code}",
        extra={
            "response_status": status_code,
            "processing_time": processing_time,
            **kwargs
        }
    )