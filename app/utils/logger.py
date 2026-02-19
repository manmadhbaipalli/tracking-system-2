"""Centralized structured JSON logging with context variables."""

import json
import logging
from contextvars import ContextVar
from datetime import datetime

request_id_context: ContextVar[str] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add request ID if available
        if request_id := request_id_context.get():
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance."""
    logger = logging.getLogger(name)
    return logger


def setup_logging(log_level: str = "INFO") -> None:
    """Initialize logging system."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Apply JSON formatter to all handlers
    for handler in logging.root.handlers:
        handler.setFormatter(JSONFormatter())


def set_request_id(request_id: str) -> None:
    """Set request ID in context."""
    request_id_context.set(request_id)


def get_request_id() -> str:
    """Get request ID from context."""
    return request_id_context.get()
