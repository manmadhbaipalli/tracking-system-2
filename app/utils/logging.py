"""
Centralized logging configuration with structured logging using structlog.

Features:
- Structured JSON logging for production
- Human-readable formatting for development
- Request correlation IDs
- Performance metrics logging
- Security event logging
"""

import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime

import structlog
from structlog.types import Processor

from app.core.config import settings


def configure_logging():
    """Configure structured logging for the application."""

    # Common processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.environment == "development":
        # Development: human-readable format
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
        wrapper_class = structlog.make_filtering_bound_logger(logging.INFO)
    else:
        # Production: JSON format
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
        wrapper_class = structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        )

    structlog.configure(
        processors=processors,
        wrapper_class=wrapper_class,
        logger_factory=structlog.WriteLoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_performance(
    logger: structlog.BoundLogger,
    operation: str,
    duration: float,
    additional_data: Optional[Dict[str, Any]] = None
):
    """Log performance metrics for operations."""
    log_data = {
        "operation": operation,
        "duration_seconds": duration,
        "performance": True,
    }

    if additional_data:
        log_data.update(additional_data)

    if duration > settings.api_timeout_seconds:
        logger.warning("Slow operation detected", **log_data)
    else:
        logger.info("Operation completed", **log_data)


def log_security_event(
    logger: structlog.BoundLogger,
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log security-related events."""
    log_data = {
        "security_event": True,
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if user_id:
        log_data["user_id"] = user_id
    if ip_address:
        log_data["ip_address"] = ip_address
    if details:
        log_data.update(details)

    logger.warning("Security event", **log_data)


def log_business_event(
    logger: structlog.BoundLogger,
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log business-related events for audit trail."""
    log_data = {
        "business_event": True,
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if entity_type:
        log_data["entity_type"] = entity_type
    if entity_id:
        log_data["entity_id"] = entity_id
    if user_id:
        log_data["user_id"] = user_id
    if details:
        log_data.update(details)

    logger.info("Business event", **log_data)


def log_external_service_call(
    logger: structlog.BoundLogger,
    service_name: str,
    endpoint: str,
    method: str,
    duration: float,
    status_code: Optional[int] = None,
    error: Optional[str] = None
):
    """Log external service API calls."""
    log_data = {
        "external_service_call": True,
        "service_name": service_name,
        "endpoint": endpoint,
        "method": method,
        "duration_seconds": duration,
    }

    if status_code:
        log_data["status_code"] = status_code
    if error:
        log_data["error"] = error

    if error or (status_code and status_code >= 400):
        logger.error("External service call failed", **log_data)
    elif duration > 5.0:  # Slow external call
        logger.warning("Slow external service call", **log_data)
    else:
        logger.info("External service call", **log_data)


class CorrelationIDProcessor:
    """Processor to add correlation ID to all log messages."""

    def __call__(self, logger, method_name, event_dict):
        # Try to get correlation ID from context variables
        correlation_id = structlog.contextvars.get_contextvars().get("correlation_id")
        if correlation_id:
            event_dict["correlation_id"] = correlation_id
        return event_dict


class SensitiveDataFilter:
    """Filter out sensitive data from log messages."""

    SENSITIVE_FIELDS = {
        "password", "token", "secret", "key", "authorization",
        "ssn", "social_security_number", "tax_id", "credit_card"
    }

    def __call__(self, logger, method_name, event_dict):
        """Filter sensitive data from event dictionary."""
        filtered_dict = {}

        for key, value in event_dict.items():
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                if isinstance(value, str) and len(value) > 4:
                    # Show only last 4 characters for sensitive strings
                    filtered_dict[key] = f"***{value[-4:]}"
                else:
                    filtered_dict[key] = "***"
            else:
                filtered_dict[key] = value

        return filtered_dict