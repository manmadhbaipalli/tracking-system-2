"""Structured logging configuration with JSON formatting."""
import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import Request

from app.core.config import settings

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': correlation_id.get(''),
        }

        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                             'pathname', 'filename', 'module', 'lineno',
                             'funcName', 'created', 'msecs', 'relativeCreated',
                             'thread', 'threadName', 'processName', 'process',
                             'exc_info', 'exc_text', 'stack_info']:
                    # Filter sensitive data
                    if isinstance(value, str) and any(sensitive in key.lower()
                                                    for sensitive in ['password', 'token', 'secret', 'key']):
                        log_obj[key] = '***FILTERED***'
                    else:
                        log_obj[key] = value

        return json.dumps(log_obj)


def setup_logging() -> None:
    """Set up structured logging."""
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        handlers=[handler]
    )

    # Set levels for third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id.get('')


def set_correlation_id(cid: str) -> None:
    """Set correlation ID for current context."""
    correlation_id.set(cid)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


class CorrelationMiddleware:
    """Middleware to add correlation IDs to requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate or extract correlation ID
            headers = dict(scope.get("headers", []))
            cid = headers.get(b"x-correlation-id", b"").decode() or generate_correlation_id()
            set_correlation_id(cid)

            # Add correlation ID to response headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = message.get("headers", [])
                    headers.append([b"x-correlation-id", cid.encode()])
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)