"""Custom exception hierarchy for consistent error handling."""


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, detail: str, error_code: str, status_code: int = 500):
        """Initialize app exception with detail, error code, and HTTP status."""
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(detail)


class AuthException(AppException):
    """General authentication failures."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail, "AUTH_ERROR", 401)


class InvalidCredentialsException(AuthException):
    """Invalid login credentials."""

    def __init__(self):
        super().__init__("Invalid credentials")
        self.error_code = "INVALID_CREDENTIALS"


class UserAlreadyExistsException(AppException):
    """User already exists (duplicate email/username)."""

    def __init__(self, field: str = "user"):
        super().__init__(f"{field} already exists", "USER_ALREADY_EXISTS", 409)


class TokenExpiredException(AuthException):
    """JWT token has expired."""

    def __init__(self):
        super().__init__("Token has expired")
        self.error_code = "TOKEN_EXPIRED"


class ValidationException(AppException):
    """Input validation error."""

    def __init__(self, detail: str):
        super().__init__(detail, "VALIDATION_ERROR", 400)


class DatabaseException(AppException):
    """Database operation error."""

    def __init__(self, detail: str = "Database error"):
        super().__init__(detail, "DATABASE_ERROR", 500)


class CircuitBreakerOpenException(AppException):
    """Circuit breaker is open - service unavailable."""

    def __init__(self):
        super().__init__("Service unavailable", "SERVICE_UNAVAILABLE", 503)


class UserNotFoundException(AppException):
    """User not found."""

    def __init__(self):
        super().__init__("User not found", "USER_NOT_FOUND", 404)


class UserInactiveException(AuthException):
    """User account is inactive."""

    def __init__(self):
        super().__init__("User account is inactive")
        self.error_code = "USER_INACTIVE"
        self.status_code = 403
