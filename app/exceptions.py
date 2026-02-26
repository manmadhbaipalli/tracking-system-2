from typing import Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, error_code: str = "APP_ERROR", status_code: int = 500) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class AuthException(AppException):
    """Authentication/authorization failure."""

    def __init__(self, message: str = "Authentication failed", error_code: str = "AUTH_ERROR") -> None:
        super().__init__(message=message, error_code=error_code, status_code=401)


class ForbiddenException(AppException):
    """Access forbidden."""

    def __init__(self, message: str = "Forbidden", error_code: str = "FORBIDDEN") -> None:
        super().__init__(message=message, error_code=error_code, status_code=403)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Not found", error_code: str = "NOT_FOUND") -> None:
        super().__init__(message=message, error_code=error_code, status_code=404)


class ConflictException(AppException):
    """Resource conflict (e.g. duplicate email)."""

    def __init__(self, message: str = "Conflict", error_code: str = "CONFLICT") -> None:
        super().__init__(message=message, error_code=error_code, status_code=409)


class ValidationException(AppException):
    """Input validation error."""

    def __init__(self, message: str = "Validation error", error_code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message=message, error_code=error_code, status_code=422)
