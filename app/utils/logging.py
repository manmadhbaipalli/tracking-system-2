"""Logging configuration for the application."""

import logging
from app.config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_format = "[%(asctime)s] %(levelname)s [%(name)s] %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
