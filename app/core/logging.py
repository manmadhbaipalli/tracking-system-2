"""Centralized logging configuration with structured JSON format"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import Request, Response
import time

from ..config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            str: JSON formatted log entry
        """
        # Base log data
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
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id

        # Add request context if available
        if hasattr(record, 'request_context'):
            log_data['request'] = record.request_context

        # Add extra fields from record
        extra_fields = {
            key: value for key, value in record.__dict__.items()
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'message', 'correlation_id', 'request_context'
            }
        }

        if extra_fields:
            log_data['extra'] = extra_fields

        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


def configure_logging() -> None:
    """Configure application logging with JSON format"""
    # Create JSON formatter
    json_formatter = JSONFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers_config = {
        'uvicorn': logging.WARNING,
        'uvicorn.access': logging.INFO,
        'sqlalchemy.engine': logging.WARNING,
        'sqlalchemy.pool': logging.WARNING,
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    # Set our app logger to INFO or DEBUG based on settings
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)


class CorrelationIDMiddleware:
    """Middleware to add correlation IDs to requests"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Add to scope for access in routes
        scope["correlation_id"] = correlation_id

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-correlation-id"] = correlation_id.encode()
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)


class LoggingMiddleware:
    """Middleware for request/response logging"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get correlation ID from scope
        correlation_id = scope.get("correlation_id", "unknown")

        # Create request context
        request_context = {
            "method": scope.get("method"),
            "path": scope.get("path"),
            "query_string": scope.get("query_string", b"").decode(),
            "client_host": scope.get("client", [None])[0] if scope.get("client") else None,
            "user_agent": None,  # Will be set from headers
        }

        # Extract headers for user agent
        headers = dict(scope.get("headers", []))
        if b"user-agent" in headers:
            request_context["user_agent"] = headers[b"user-agent"].decode()

        # Log request
        logger = logging.getLogger("app.requests")
        start_time = time.time()

        logger.info(
            f"Request started: {request_context['method']} {request_context['path']}",
            extra={
                "correlation_id": correlation_id,
                "request_context": request_context,
                "event": "request_start"
            }
        )

        # Response wrapper to log response details
        response_status = None

        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)

        # Call the application
        try:
            await self.app(scope, receive, send_wrapper)

            # Log successful response
            duration = time.time() - start_time
            logger.info(
                f"Request completed: {request_context['method']} {request_context['path']} - {response_status}",
                extra={
                    "correlation_id": correlation_id,
                    "request_context": request_context,
                    "response_status": response_status,
                    "duration_ms": round(duration * 1000, 2),
                    "event": "request_complete"
                }
            )

        except Exception as e:
            # Log error response
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request_context['method']} {request_context['path']} - {str(e)}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "request_context": request_context,
                    "duration_ms": round(duration * 1000, 2),
                    "event": "request_error"
                }
            )
            raise


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with correlation ID support.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_with_correlation(
    logger: logging.Logger,
    level: int,
    message: str,
    correlation_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log message with correlation ID.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        correlation_id: Optional correlation ID
        **kwargs: Additional log context
    """
    extra = kwargs.copy()
    if correlation_id:
        extra['correlation_id'] = correlation_id

    logger.log(level, message, extra=extra)