"""Global exception handler for consistent error responses."""

from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.utils.exceptions import AppException
from app.utils.logger import get_logger, get_request_id

logger = get_logger(__name__)


async def exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle all exceptions and return consistent error response."""
    request_id = get_request_id()

    # Handle known application exceptions
    if isinstance(exc, AppException):
        logger.warning(
            f"Application exception: {exc.error_code}",
            extra={
                "error_code": exc.error_code,
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": exc.error_code,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id,
            },
        )

    # Handle validation errors (from Pydantic)
    if isinstance(exc, ValidationError):
        logger.warning("Validation error", extra={"errors": exc.errors()})
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id,
            },
        )

    # Handle unexpected errors
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
        },
    )
