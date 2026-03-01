from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


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


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": exc.error_code,
            "message": exc.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
