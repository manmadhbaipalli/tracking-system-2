"""Custom exceptions and global exception handlers."""

from typing import Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.logging import get_logger

logger = get_logger("app.exceptions")


# Custom exception classes
class AuthenticationException(HTTPException):
    """Exception for authentication failures."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationException(HTTPException):
    """Exception for authorization failures."""

    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundException(HTTPException):
    """Exception for resource not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    """Exception for resource conflicts."""

    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationException(HTTPException):
    """Exception for validation errors."""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class InternalServerException(HTTPException):
    """Exception for internal server errors."""

    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


# Exception handler utilities
def create_error_response(
    status_code: int,
    message: str,
    details: Any = None,
    correlation_id: str = None
) -> Dict[str, Any]:
    """Create standardized error response."""
    error_response = {
        "error": {
            "status_code": status_code,
            "message": message,
        }
    }

    if details is not None:
        error_response["error"]["details"] = details

    if correlation_id:
        error_response["correlation_id"] = correlation_id

    return error_response


# Global exception handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException and return standardized JSON response."""
    from app.core.logging import get_correlation_id

    correlation_id = get_correlation_id()

    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url),
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=exc.detail,
            correlation_id=correlation_id
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    from app.core.logging import get_correlation_id

    correlation_id = get_correlation_id()

    logger.warning(
        "Validation error",
        extra={
            "errors": exc.errors(),
            "path": str(request.url),
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation failed",
            details=exc.errors(),
            correlation_id=correlation_id
        )
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    from app.core.logging import get_correlation_id

    correlation_id = get_correlation_id()

    logger.warning(
        "Pydantic validation error",
        extra={
            "errors": exc.errors(),
            "path": str(request.url),
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation failed",
            details=exc.errors(),
            correlation_id=correlation_id
        )
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors."""
    from app.core.logging import get_correlation_id

    correlation_id = get_correlation_id()

    logger.warning(
        "Database integrity error",
        extra={
            "error": str(exc.orig),
            "path": str(request.url),
            "method": request.method,
        }
    )

    # Check for common constraint violations
    error_message = "Database constraint violation"
    if "UNIQUE constraint failed" in str(exc.orig):
        if "users.email" in str(exc.orig):
            error_message = "Email address already exists"
        elif "users.username" in str(exc.orig):
            error_message = "Username already exists"
        else:
            error_message = "Resource already exists"

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            message=error_message,
            correlation_id=correlation_id
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    from app.core.logging import get_correlation_id

    correlation_id = get_correlation_id()

    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "error": str(exc),
            "path": str(request.url),
            "method": request.method,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            correlation_id=correlation_id
        )
    )