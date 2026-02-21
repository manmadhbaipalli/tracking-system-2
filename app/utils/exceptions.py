"""Custom exception classes for the application."""


class AppException(Exception):
    """Base exception class with status code and message."""

    def __init__(self, message: str, status_code: int = 500):
        """Initialize AppException.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, 400)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, 401)


class NotFoundError(AppException):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class ConflictError(AppException):
    """Raised when there's a conflict (e.g., duplicate email)."""

    def __init__(self, message: str = "Email already registered"):
        super().__init__(message, 409)


class ExternalServiceError(AppException):
    """Raised when external service is unavailable."""

    def __init__(self, message: str = "External service unavailable"):
        super().__init__(message, 503)
