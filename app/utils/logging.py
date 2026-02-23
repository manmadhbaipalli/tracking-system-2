"""Centralized logging configuration with structured output."""

import logging
import sys
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional
from uuid import uuid4

import structlog
from structlog.types import EventDict

from app.config import settings


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add correlation ID to log events."""
    if "correlation_id" not in event_dict:
        event_dict["correlation_id"] = str(uuid4())[:8]
    return event_dict


def drop_color_message_key(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Drop the color key to avoid redundant information."""
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        stream=sys.stdout,
        format="%(message)s",
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        drop_color_message_key,
    ]

    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=False),
        ])

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        structlog.BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


@contextmanager
def log_context(correlation_id: Optional[str] = None, **kwargs: Any) -> Generator[None, None, None]:
    """
    Context manager for adding context to all logs within the block.

    Args:
        correlation_id: Optional correlation ID
        **kwargs: Additional context to add to logs

    Yields:
        None
    """
    context: Dict[str, Any] = {}

    if correlation_id:
        context["correlation_id"] = correlation_id

    context.update(kwargs)

    with structlog.contextvars.bound_contextvars(**context):
        yield


def filter_sensitive_data(event_dict: EventDict) -> EventDict:
    """
    Filter sensitive data from log events.

    Args:
        event_dict: Log event dictionary

    Returns:
        EventDict: Filtered event dictionary
    """
    sensitive_keys = {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "jwt",
        "secret",
        "key",
        "authorization",
        "cookie",
    }

    def _filter_dict(data: Any) -> Any:
        if isinstance(data, dict):
            return {
                key: "[FILTERED]" if key.lower() in sensitive_keys else _filter_dict(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [_filter_dict(item) for item in data]
        else:
            return data

    return _filter_dict(event_dict)