from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone


class AppException(Exception):
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND", 404)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, "CONFLICT", 409)


class AuthException(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "FORBIDDEN", 403)


class RateLimitException(AppException):
    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, "RATE_LIMIT", 429)


def _get_correlation_id() -> str:
    try:
        from app.middleware import correlation_id_var
        return correlation_id_var.get("-")
    except Exception:
        return "-"


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": exc.error_code,
            "message": exc.message,
            "correlation_id": _get_correlation_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "status": 422,
            "error": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": details,
            "correlation_id": _get_correlation_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "correlation_id": _get_correlation_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
