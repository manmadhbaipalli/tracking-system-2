# Test-Design: FastAPI Authentication Service Implementation

## Executive Summary

This design document outlines the implementation approach for a complete FastAPI authentication service with advanced features including centralized logging, exception handling, circuit breaker pattern, and comprehensive Swagger documentation. The design builds on the foundational analysis and provides detailed implementation guidance for 20 source code files organized in a layered architecture.

---

## 1. Approach: Layered Service Architecture

### 1.1 Architecture Overview

The application follows a **layered service architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│     HTTP Client / Swagger UI        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  FastAPI Application with Middleware │
│  • Exception Handler (catches all)   │
│  • Request Logging (UUID, timing)    │
│  • CORS Configuration                │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│     Routes Layer (HTTP Interface)    │
│  • /auth/register                    │
│  • /auth/login                       │
│  • /auth/refresh                     │
│  • /health                           │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  Dependency Injection Layer          │
│  • get_db_session()                  │
│  • get_current_user()                │
│  • get_request_id()                  │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    Services Layer (Business Logic)   │
│  • AuthService                       │
│  • UserService                       │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Utils Layer (Cross-cutting)        │
│  • JWT tokens                        │
│  • Password hashing                  │
│  • Logging (structured JSON)         │
│  • Exception handling                │
│  • Circuit breaker                   │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Data Layer (Database Access)       │
│  • SQLAlchemy ORM                    │
│  • Pydantic schemas                  │
│  • Async session management          │
└────────────────┬────────────────────┘
                 │
        ┌────────▼────────┐
        │   SQLite/PgSQL   │
        └──────────────────┘
```

### 1.2 Key Design Principles

1. **Layered Separation**: Each layer has a single responsibility
2. **Dependency Injection**: FastAPI's `Depends()` for loose coupling
3. **Async-First**: All I/O operations are async
4. **Structured Logging**: JSON logs with request IDs for traceability
5. **Explicit Error Handling**: Custom exceptions with proper HTTP status codes
6. **Resilience**: Circuit breaker pattern for external service calls
7. **Security-First**: Password hashing, JWT tokens, sensitive data redaction

---

## 2. Detailed Changes: File-by-File Implementation

### Phase 1: Utilities Foundation (No Dependencies)

#### 2.1 `app/utils/exceptions.py` (NEW)
**Purpose**: Custom exception hierarchy for consistent error handling

**Content Structure**:
```python
class AppException(Exception):
    """Base exception for all application errors"""
    def __init__(self, detail: str, error_code: str, status_code: int = 500):
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code

class AuthException(AppException):
    """General authentication failures"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail, "AUTH_ERROR", 401)

class InvalidCredentialsException(AuthException):
    """Invalid login credentials"""
    def __init__(self):
        super().__init__("Invalid credentials")
        self.error_code = "INVALID_CREDENTIALS"

class UserAlreadyExistsException(AppException):
    """User already exists (duplicate email/username)"""
    def __init__(self, field: str = "user"):
        super().__init__(f"{field} already exists", "USER_ALREADY_EXISTS", 409)

class TokenExpiredException(AuthException):
    """JWT token has expired"""
    def __init__(self):
        super().__init__("Token has expired")
        self.error_code = "TOKEN_EXPIRED"

class ValidationException(AppException):
    """Input validation error"""
    def __init__(self, detail: str):
        super().__init__(detail, "VALIDATION_ERROR", 400)

class DatabaseException(AppException):
    """Database operation error"""
    def __init__(self, detail: str = "Database error"):
        super().__init__(detail, "DATABASE_ERROR", 500)

class CircuitBreakerOpenException(AppException):
    """Circuit breaker is open - service unavailable"""
    def __init__(self):
        super().__init__("Service unavailable", "SERVICE_UNAVAILABLE", 503)

class UserNotFoundException(AppException):
    """User not found"""
    def __init__(self):
        super().__init__("User not found", "USER_NOT_FOUND", 404)

class UserInactiveException(AuthException):
    """User account is inactive"""
    def __init__(self):
        super().__init__("User account is inactive")
        self.error_code = "USER_INACTIVE"
        self.status_code = 403
```

**Key Features**:
- Base exception with detail, error_code, status_code
- Specific exception types for each error scenario
- HTTP status codes tied to exceptions (400, 401, 403, 404, 409, 500, 503)
- Error codes for API consumers to handle programmatically

---

#### 2.2 `app/utils/logger.py` (NEW)
**Purpose**: Centralized structured JSON logging with context variables

**Content Structure**:
```python
import logging
import json
from datetime import datetime
from contextvars import ContextVar

request_id_context: ContextVar[str] = ContextVar('request_id', default=None)

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON"""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        }

        # Add request ID if available
        if request_id := request_id_context.get():
            log_data['request_id'] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance"""
    logger = logging.getLogger(name)
    return logger

def setup_logging(log_level: str = "INFO") -> None:
    """Initialize logging system"""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(message)s',
        handlers=[logging.StreamHandler()]
    )

    # Apply JSON formatter to all handlers
    for handler in logging.root.handlers:
        handler.setFormatter(JSONFormatter())

def set_request_id(request_id: str) -> None:
    """Set request ID in context"""
    request_id_context.set(request_id)

def get_request_id() -> str:
    """Get request ID from context"""
    return request_id_context.get()
```

**Key Features**:
- JSON output format with timestamp, level, message, logger name
- Context variables for request ID propagation
- Custom JSONFormatter for structured logging
- Request ID injection into all log entries
- No sensitive data logged (passwords, tokens)

---

#### 2.3 `app/utils/password.py` (NEW)
**Purpose**: Password hashing and verification using bcrypt

**Content Structure**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)
```

**Key Features**:
- Bcrypt with automatic work factor handling
- Timing-safe verification via passlib
- Simple, focused API
- Each hash unique due to salt

---

#### 2.4 `app/utils/circuit_breaker.py` (NEW)
**Purpose**: Circuit breaker pattern for resilience

**Content Structure**:
```python
from enum import Enum
from time import time
from threading import Lock
from app.utils.exceptions import CircuitBreakerOpenException
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for service resilience"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: float = None
        self.state = CircuitState.CLOSED
        self._lock = Lock()

    def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenException()

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        return time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call"""
        with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info("Circuit breaker transitioning to CLOSED")

    def _on_failure(self) -> None:
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker transitioning to OPEN after {self.failure_count} failures")

    def reset(self) -> None:
        """Manually reset the circuit breaker"""
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker manually reset to CLOSED")
```

**Key Features**:
- Three states: CLOSED (normal), OPEN (fail fast), HALF_OPEN (recovery)
- Configurable failure threshold and recovery timeout
- Thread-safe state transitions
- Logging on state changes
- Generic exception handling

---

#### 2.5 `app/utils/__init__.py` (NEW)
Empty package initializer.

---

### Phase 2: Middleware Layer

#### 2.6 `app/middleware/exception.py` (NEW)
**Purpose**: Global exception handler for consistent error responses

**Content Structure**:
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.exceptions import AppException
from app.utils.logger import get_logger, get_request_id

logger = get_logger(__name__)

async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all exceptions and return consistent error response"""

    request_id = get_request_id()

    # Handle known application exceptions
    if isinstance(exc, AppException):
        logger.warning(
            f"Application exception: {exc.error_code}",
            extra={
                'error_code': exc.error_code,
                'detail': exc.detail,
                'status_code': exc.status_code
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'detail': exc.detail,
                'error_code': exc.error_code,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': request_id
            }
        )

    # Handle validation errors (from Pydantic)
    if isinstance(exc, RequestValidationError):
        logger.warning("Validation error", extra={'errors': exc.errors()})
        return JSONResponse(
            status_code=400,
            content={
                'detail': 'Validation error',
                'error_code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': request_id
            }
        )

    # Handle unexpected errors
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            'detail': 'Internal server error',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'request_id': request_id
        }
    )
```

**Key Features**:
- Catches all exceptions
- Custom exceptions return proper status codes and error codes
- Validation errors return 400
- Unexpected errors return 500 without stack traces
- All responses include request_id for tracing
- Logging on error with context

---

#### 2.7 `app/middleware/logging.py` (NEW)
**Purpose**: Request/response logging middleware with request ID generation

**Content Structure**:
```python
import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.utils.logger import get_logger, set_request_id

logger = get_logger(__name__)

SKIP_LOGGING_PATHS = {'/health', '/docs', '/redoc', '/openapi.json'}

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with request ID"""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log incoming request and outgoing response"""

        # Generate request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        # Skip logging for health/docs endpoints
        if request.url.path in SKIP_LOGGING_PATHS:
            response = await call_next(request)
            return response

        # Log incoming request
        start_time = time.time()
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'query_string': request.url.query
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log outgoing response
        logger.info(
            f"Outgoing response: {response.status_code}",
            extra={
                'status_code': response.status_code,
                'duration_ms': duration_ms
            }
        )

        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id

        return response
```

**Key Features**:
- Generates unique request ID (UUID) for each request
- Logs request method, path, query string
- Logs response status code and duration
- Skips health checks and documentation endpoints
- Adds request ID to response headers for client reference
- Request ID propagated via context variable

---

#### 2.8 `app/middleware/__init__.py` (NEW)
Empty package initializer.

---

### Phase 3: JWT and Dependencies

#### 2.9 `app/utils/jwt.py` (NEW)
**Purpose**: JWT token generation, validation, and user ID extraction

**Content Structure**:
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import settings
from app.utils.exceptions import TokenExpiredException
from app.utils.logger import get_logger

logger = get_logger(__name__)

def create_access_token(user_id: int, expires_delta: timedelta = None) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        'sub': str(user_id),
        'exp': expire,
        'type': 'access'
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(user_id: int, expires_delta: timedelta = None) -> str:
    """Create a JWT refresh token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        'sub': str(user_id),
        'exp': expire,
        'type': 'refresh'
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise TokenExpiredException()

def extract_user_id_from_token(token: str) -> int:
    """Extract user ID from a JWT token"""
    payload = verify_token(token)
    user_id = payload.get('sub')
    if not user_id:
        raise TokenExpiredException()
    return int(user_id)
```

**Key Features**:
- Separate access and refresh tokens with different expirations
- Access tokens: 15-30 minutes (configurable)
- Refresh tokens: 7 days (configurable)
- Token type ('access' or 'refresh') included in payload
- JWTError caught and converted to TokenExpiredException
- Logging on verification failures

---

#### 2.10 `app/dependencies.py` (NEW)
**Purpose**: Dependency injection for FastAPI routes

**Content Structure**:
```python
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session as _get_db_session
from app.utils.jwt import verify_token, extract_user_id_from_token
from app.utils.exceptions import TokenExpiredException, InvalidCredentialsException
from app.utils.logger import get_logger, get_request_id
from app.services.user_service import UserService
from app.models.user import User

logger = get_logger(__name__)

async def get_db_session() -> AsyncSession:
    """Provide database session"""
    async with _get_db_session() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> User:
    """Get current authenticated user from JWT token"""
    try:
        user_id = extract_user_id_from_token(token)
    except TokenExpiredException:
        logger.warning("Invalid token in authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    user_service = UserService(session)
    user = await user_service.get_user_by_id(user_id)

    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return user

async def get_request_id() -> str:
    """Get current request ID"""
    return get_request_id()
```

**Key Features**:
- Provides database sessions to routes
- Validates JWT tokens and returns current user
- HTTP 401 for invalid/expired tokens
- Generic error messages (don't reveal whether user exists)
- Integration with UserService for database queries

---

### Phase 4: Services Layer

#### 2.11 `app/services/__init__.py` (NEW)
Empty package initializer.

---

#### 2.12 `app/services/user_service.py` (NEW)
**Purpose**: User management business logic

**Content Structure**:
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.utils.exceptions import UserAlreadyExistsException, UserNotFoundException
from app.utils.logger import get_logger

logger = get_logger(__name__)

class UserService:
    """Service for user management operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User:
        """Get user by username"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        username: str,
        email: str,
        hashed_password: str
    ) -> User:
        """Create a new user"""
        user = User(
            username=username,
            email=email.lower(),
            hashed_password=hashed_password,
            is_active=True
        )

        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"User created: {user.id}")
            return user
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"User creation failed - duplicate: {email}")
            if 'username' in str(e):
                raise UserAlreadyExistsException('username')
            elif 'email' in str(e):
                raise UserAlreadyExistsException('email')
            raise UserAlreadyExistsException()
```

**Key Features**:
- CRUD operations for users
- Query by ID, email, username
- Email case-insensitive lookup
- Handles IntegrityError for duplicate constraints
- Proper exception mapping (409 Conflict for duplicates)
- Logging on success and failure

---

#### 2.13 `app/services/auth_service.py` (NEW)
**Purpose**: Authentication business logic

**Content Structure**:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import TokenResponse, UserResponse
from app.models.user import User
from app.services.user_service import UserService
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token, extract_user_id_from_token
from app.utils.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    TokenExpiredException,
    ValidationException
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    """Service for authentication operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)

    async def register_user(
        self,
        email: str,
        username: str,
        password: str
    ) -> TokenResponse:
        """Register a new user"""
        # Validate input
        if not email or not username or not password:
            raise ValidationException("Missing required fields")

        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters")

        # Check if user already exists
        existing_by_email = await self.user_service.get_user_by_email(email)
        if existing_by_email:
            logger.warning(f"Registration failed - email exists: {email}")
            raise UserAlreadyExistsException('email')

        existing_by_username = await self.user_service.get_user_by_username(username)
        if existing_by_username:
            logger.warning(f"Registration failed - username exists: {username}")
            raise UserAlreadyExistsException('username')

        # Hash password and create user
        hashed_password = hash_password(password)
        user = await self.user_service.create_user(username, email, hashed_password)

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        logger.info(f"User registered: {user.id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer',
            user=UserResponse.from_orm(user)
        )

    async def login(
        self,
        email: str = None,
        username: str = None,
        password: str = None
    ) -> TokenResponse:
        """Authenticate user and return tokens"""
        if not password:
            raise InvalidCredentialsException()

        if not email and not username:
            raise InvalidCredentialsException()

        # Find user by email or username
        user = None
        if email:
            user = await self.user_service.get_user_by_email(email)
        elif username:
            user = await self.user_service.get_user_by_username(username)

        # Verify credentials (generic error message)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Login failed - invalid credentials")
            raise InvalidCredentialsException()

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed - user inactive: {user.id}")
            raise InvalidCredentialsException()

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        logger.info(f"User login successful: {user.id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer',
            user=UserResponse.from_orm(user)
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Generate new access token using refresh token"""
        try:
            user_id = extract_user_id_from_token(refresh_token)
        except TokenExpiredException:
            logger.warning("Refresh token validation failed")
            raise InvalidCredentialsException()

        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Refresh failed - user not found: {user_id}")
            raise InvalidCredentialsException()

        # Generate new access token
        access_token = create_access_token(user.id)

        logger.info(f"Access token refreshed: {user.id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer',
            user=UserResponse.from_orm(user)
        )
```

**Key Features**:
- User registration with validation
- Login with email or username
- Password verification using bcrypt
- Token generation (access + refresh)
- Generic error messages for security
- Proper exception mapping
- Comprehensive logging

---

### Phase 5: Routes Layer

#### 2.14 `app/routes/__init__.py` (NEW)
Empty package initializer.

---

#### 2.15 `app/routes/auth.py` (NEW)
**Purpose**: Authentication API endpoints

**Content Structure**:
```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import UserRegister, UserLogin, TokenResponse
from app.services.auth_service import AuthService
from app.dependencies import get_db_session
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_db_session)
) -> TokenResponse:
    """
    Register a new user

    - **email**: User email address
    - **username**: Unique username
    - **password**: Password (min 8 characters)

    Returns access and refresh tokens along with user info
    """
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_db_session)
) -> TokenResponse:
    """
    Login user

    - **email** (optional): User email
    - **username** (optional): User username
    - **password**: User password

    Requires either email or username. Returns tokens and user info.
    """
    auth_service = AuthService(session)
    return await auth_service.login(
        email=credentials.email,
        username=credentials.username,
        password=credentials.password
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str,
    session: AsyncSession = Depends(get_db_session)
) -> TokenResponse:
    """
    Refresh access token

    - **refresh_token**: Valid refresh token

    Returns new access token with same refresh token
    """
    auth_service = AuthService(session)
    return await auth_service.refresh_access_token(refresh_token)
```

**Key Features**:
- POST /auth/register (201 Created)
- POST /auth/login (200 OK)
- POST /auth/refresh (200 OK)
- Pydantic request/response validation
- Proper status codes
- Comprehensive docstrings for Swagger
- Dependency injection for session

---

#### 2.16 `app/routes/health.py` (NEW)
**Purpose**: Health check endpoint

**Content Structure**:
```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health", status_code=200)
async def health_check() -> dict:
    """
    Health check endpoint

    Used by load balancers and monitoring systems to verify service is running.
    Returns 200 if healthy.
    """
    return {"status": "healthy"}
```

**Key Features**:
- Simple GET /health endpoint
- Returns 200 status
- Excluded from detailed logging
- Used for load balancer checks

---

### Phase 6: Main Application

#### 2.17 `app/main.py` (NEW)
**Purpose**: FastAPI application entry point with middleware and routes

**Content Structure**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, init_db
from app.middleware.logging import LoggingMiddleware
from app.middleware.exception import exception_handler
from app.utils.exceptions import AppException
from app.utils.logger import setup_logging
from app.routes import auth, health

# Initialize logging
setup_logging(settings.LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title="Authentication Service",
    description="FastAPI service with authentication, logging, exception handling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Register middleware (order matters!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handler
app.add_exception_handler(AppException, exception_handler)
app.add_exception_handler(Exception, exception_handler)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(health.router)

# Startup event
@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await init_db()

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown"""
    await engine.dispose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Key Features**:
- FastAPI app with metadata
- Swagger UI at /docs
- ReDoc at /redoc
- OpenAPI schema at /openapi.json
- Middleware stack (CORS → Logging → Exception handling)
- Database initialization on startup
- Router registration
- Graceful shutdown

---

### Phase 7: Configuration and Schema Updates

#### 2.18 `app/config.py` (UPDATE)
**Additions**:
- CORS origins configuration
- JWT configuration (access/refresh expiration)
- Circuit breaker configuration
- Log level configuration

**New Content** (additions):
```python
# Add to existing config.py
class Settings(BaseSettings):
    # ... existing fields ...

    # CORS Configuration
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]

    # JWT Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS: int = 1

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
```

---

#### 2.19 `app/models/schemas.py` (UPDATE)
**Additions**:
- ErrorResponse schema for consistent error format
- TokenResponse schema (may already exist, ensure correct)
- UserResponse schema (may already exist)

**New Content** (additions):
```python
# Add to existing schemas.py
from datetime import datetime

class ErrorResponse(BaseModel):
    """Standard error response format"""
    detail: str
    error_code: str
    timestamp: datetime
    request_id: str

class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserResponse(BaseModel):
    """User information response"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # For ORM compatibility
```

---

#### 2.20 `app/database.py` (UPDATE)
**Addition**:
- Add `init_db()` async function for table creation

**New Function**:
```python
async def init_db() -> None:
    """Initialize database and create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

---

## 3. Interfaces & API Contracts

### 3.1 Authentication Endpoints

#### POST /auth/register
**Request**:
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepass123"
}
```

**Success Response (201 Created)**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "user@example.com",
    "is_active": true,
    "created_at": "2024-01-15T10:30:45Z"
  }
}
```

**Error Responses**:
- 400 Bad Request (validation error)
- 409 Conflict (duplicate email/username)
- 500 Internal Server Error

#### POST /auth/login
**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

**OR**:
```json
{
  "username": "johndoe",
  "password": "securepass123"
}
```

**Success Response (200 OK)**: Same as register

**Error Responses**:
- 400 Bad Request (missing credentials)
- 401 Unauthorized (invalid credentials or inactive user)
- 500 Internal Server Error

#### POST /auth/refresh
**Request**:
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Success Response (200 OK)**: TokenResponse with new access token

**Error Responses**:
- 401 Unauthorized (invalid or expired refresh token)
- 500 Internal Server Error

#### GET /health
**Success Response (200 OK)**:
```json
{
  "status": "healthy"
}
```

### 3.2 Error Response Format
```json
{
  "detail": "Invalid credentials",
  "error_code": "INVALID_CREDENTIALS",
  "timestamp": "2024-01-15T10:30:45Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 4. Trade-offs & Design Decisions

### Decision 1: Stateless JWT Authentication
**Choice**: Use stateless JWT tokens without session storage

**Rationale**:
- Simpler to implement and scale
- No session database needed
- Standard for REST APIs
- Works well with distributed systems

**Trade-offs**:
- Cannot revoke tokens immediately
- Token remains valid until expiration

**Mitigation**: Use short access token lifetimes (15-30 min)

### Decision 2: Generic Error Messages
**Choice**: Return same error message for login failures (invalid credentials vs. user not found)

**Rationale**:
- Security best practice
- Prevents user enumeration attacks
- Consistent with industry standards

**Trade-offs**:
- Users might not know if email is registered
- Slightly less helpful for legitimate users

**Mitigation**: None needed - security takes priority

### Decision 3: Async-First Implementation
**Choice**: All operations use async/await with SQLAlchemy async ORM

**Rationale**:
- FastAPI is async-first framework
- Better resource utilization
- Non-blocking I/O
- Handles concurrent requests efficiently

**Trade-offs**:
- More complex code patterns
- Requires pytest-asyncio for testing
- Steeper learning curve

**Mitigation**: Well-documented code, comprehensive tests

### Decision 4: Structured JSON Logging
**Choice**: All logs in JSON format with structured fields

**Rationale**:
- Machine-parseable format
- Integrates with log aggregation tools (ELK, Datadog, etc.)
- Standard for cloud deployments
- Better for searching and filtering

**Trade-offs**:
- Less human-readable in console
- Requires special tooling for log visualization

**Mitigation**: Use log aggregation tools in production

### Decision 5: Service Pattern (Not Pure Repository)
**Choice**: Services contain business logic and interact with database directly via UserService

**Rationale**:
- Clear separation of concerns
- Simpler than full repository pattern
- Adequate for this project scope
- Easier to test

**Trade-offs**:
- Not as flexible as pure repository pattern
- Database access tied to service implementation

**Mitigation**: Services abstract the details from routes

---

## 5. Open Questions & Implementation Notes

### For Implementation Agent

1. **OAuth2 Scheme**: Should use `HTTPBearer` or custom scheme for token validation?
   - Current design: HTTPBearer via `oauth2_scheme` in dependencies.py
   - Alternative: Custom Bearer scheme
   - **Decision**: Use HTTPBearer - it's standard and integrates with Swagger

2. **Database Migrations**: Should use Alembic or direct schema creation?
   - Current design: Direct schema creation via `init_db()`
   - Alternative: Use Alembic for versioned migrations
   - **Decision**: Direct schema creation for simplicity; Alembic not required for MVP

3. **Rate Limiting**: Should implement before this phase?
   - Current design: Not implemented, noted as "future"
   - Alternative: Add simple rate limiter middleware
   - **Decision**: Out of scope for this phase, can be added later

4. **Email Validation**: Should use email-validator library?
   - Current design: Basic Pydantic validation
   - Alternative: Use email-validator library
   - **Decision**: Pydantic's built-in EmailStr should be sufficient

5. **Password Requirements**: Should enforce complexity rules?
   - Current design: Minimum 8 characters
   - Alternative: Add uppercase, lowercase, digits, special chars
   - **Decision**: Keep simple for MVP; add complexity in Phase 2

---

## 6. Implementation Sequence

The implementation should follow this order to respect dependencies:

1. **Phase 1**: Utilities (exceptions, logger, password, circuit_breaker)
2. **Phase 2**: JWT and JWT-based utilities
3. **Phase 3**: Middleware (exception handler, logging)
4. **Phase 4**: Services (user_service, auth_service)
5. **Phase 5**: Dependencies injection configuration
6. **Phase 6**: Routes (auth routes, health route)
7. **Phase 7**: Main application file
8. **Phase 8**: Configuration and schema updates

This sequence ensures each module has all its dependencies available before being used.

---

## 7. Testing Strategy Summary

### Unit Tests (~400 lines)
- Password hashing and verification (5 tests)
- JWT token creation and validation (8 tests)
- Exception types and error codes (5 tests)
- Circuit breaker state transitions (10 tests)
- User service queries and creation (6 tests)
- Auth service registration, login, refresh (8 tests)

### Integration Tests (~600 lines)
- POST /auth/register (success, validation, duplicate)
- POST /auth/login (success, invalid credentials, inactive user)
- POST /auth/refresh (success, invalid token, expired token)
- GET /health (success, status code)
- Middleware functionality (request logging, exception handling)
- Swagger documentation availability

### Test Coverage Goal: 85%+

---

## 8. Success Criteria

✅ **All functional requirements met**:
- Registration endpoint with validation
- Login endpoint with email/username support
- Token refresh endpoint
- Health check endpoint

✅ **All non-functional requirements met**:
- Centralized structured JSON logging
- Centralized exception handling
- Circuit breaker pattern implemented
- Swagger/OpenAPI documentation complete

✅ **Code quality**:
- PEP 8 compliant
- Full type hints
- Comprehensive tests (85%+ coverage)
- All tests passing

✅ **Security**:
- Passwords hashed with bcrypt
- JWT tokens with expiration
- Generic error messages (no user enumeration)
- Sensitive data redacted from logs

---

## 9. Summary

This design provides a complete blueprint for implementing a production-ready FastAPI authentication service with:

- **20 source code files** organized in a layered architecture
- **Clear separation of concerns**: Routes → Services → Utils → Database
- **Comprehensive error handling**: Custom exceptions with proper HTTP status codes
- **Structured logging**: JSON format with request ID propagation
- **Resilience**: Circuit breaker pattern for external services
- **Security**: Password hashing, JWT tokens, generic error messages
- **Documentation**: Automatic Swagger/OpenAPI generation
- **Testability**: Designed for 85%+ code coverage with unit and integration tests

The implementation can proceed phase-by-phase with clear dependencies and no blocking issues.
