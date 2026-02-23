"""Custom exceptions for business logic and error handling."""


class AuthServiceException(Exception):
    """Base exception for all auth service errors."""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(AuthServiceException):
    """Raised when business rule validation fails."""

    def __init__(self, message: str = "Validation error occurred"):
        super().__init__(message, "VALIDATION_ERROR")


class AuthenticationError(AuthServiceException):
    """Raised when authentication fails (invalid credentials)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(AuthServiceException):
    """Raised when authorization fails (insufficient permissions)."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class UserNotFoundError(AuthServiceException):
    """Raised when a user is not found."""

    def __init__(self, message: str = "User not found"):
        super().__init__(message, "USER_NOT_FOUND")


class UserAlreadyExistsError(AuthServiceException):
    """Raised when trying to create a user that already exists."""

    def __init__(self, message: str = "User already exists"):
        super().__init__(message, "USER_ALREADY_EXISTS")


class DatabaseError(AuthServiceException):
    """Raised when database operations fail."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR")


class CircuitBreakerError(AuthServiceException):
    """Raised when circuit breaker is open and requests are being rejected."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, "CIRCUIT_BREAKER_OPEN")


class TokenError(AuthServiceException):
    """Raised when JWT token operations fail."""

    def __init__(self, message: str = "Token operation failed"):
        super().__init__(message, "TOKEN_ERROR")


class RateLimitError(AuthServiceException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")