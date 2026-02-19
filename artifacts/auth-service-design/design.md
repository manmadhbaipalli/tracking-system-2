# Auth Service Technical Design

**Date**: 2026-02-19
**Phase**: Design
**Task**: auth-service-design
**Status**: Ready for Implementation

---

## 1. Approach: High-Level Solution Strategy

### Overall Architecture
We will implement a production-grade FastAPI-based authentication microservice following a **layered architecture** pattern:

1. **API Layer** (Routers): Handle HTTP requests, validate inputs, delegate to services
2. **Service Layer** (Business Logic): Implement authentication flows, rate limiting, account management
3. **Data Layer** (ORM/Database): SQLAlchemy models and database operations
4. **Cross-cutting Concerns**: Logging middleware, exception handlers, circuit breaker, security utilities

### Key Design Decisions

**1. Async-First Architecture**
- Use `async`/`await` throughout for I/O operations
- Leverage FastAPI's async capabilities for concurrency
- Database operations via SQLAlchemy async ORM with asyncpg

**2. Service Layer Abstraction**
- Separate business logic from HTTP routing
- Makes testing easier (unit test services independently)
- Enables code reuse across endpoints

**3. Centralized Error Handling**
- Custom exception classes for domain-specific errors
- Global exception handlers for consistent JSON responses
- Include error codes and request IDs for debugging

**4. Structured Logging**
- JSON-formatted logs for log aggregation
- Middleware injects request IDs for tracing
- Log security events and authentication attempts

**5. Circuit Breaker Pattern**
- Prevent cascading failures for external service calls
- Three states: CLOSED (normal), OPEN (failing), HALF_OPEN (testing)
- Configurable thresholds and recovery timeouts

---

## 2. Detailed Changes: File-by-File Breakdown

### Configuration & Setup

#### `requirements.txt`
- List all Python dependencies with pinned versions
- FastAPI, SQLAlchemy, Pydantic, security libraries, testing tools
- **Status**: Create new

#### `.env.example`
- Template environment variables
- Database credentials, JWT secrets, circuit breaker settings, logging level
- **Status**: Create new

#### `app/__init__.py`
- Empty init file for package recognition
- **Status**: Create new

---

### Core Application Structure

#### `app/main.py` (~150 lines)
**Purpose**: FastAPI app initialization, middleware setup, exception handlers

**Contents**:
- Create FastAPI app instance with title and version
- Register middleware: logging, CORS
- Register exception handlers for all custom exceptions
- Add startup/shutdown event handlers
- Include routers (auth router)
- Root health check endpoint

**Key Features**:
```python
from fastapi import FastAPI
from app.routers import auth
from app.handlers.exceptions import setup_exception_handlers
from app.middleware.logging import LoggingMiddleware

app = FastAPI(title="Auth Service", version="1.0.0")

# Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(CORSMiddleware, ...)

# Exception handlers
setup_exception_handlers(app)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Status**: Create new

#### `app/config.py` (~60 lines)
**Purpose**: Configuration and environment variables

**Contents**:
- Settings class using Pydantic
- Load from environment variables via python-dotenv
- Database URL, JWT secrets, security settings, circuit breaker config
- Validation of required settings on startup

**Environment Variables**:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing secret
- `ALGORITHM`: JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiry time
- `MAX_LOGIN_ATTEMPTS`: Brute force threshold (default: 5)
- `LOGIN_ATTEMPT_TIMEOUT`: Timeout for attempts in seconds (default: 900 = 15 min)
- `CIRCUIT_BREAKER_FAILURE_THRESHOLD`: Failures before opening (default: 5)
- `CIRCUIT_BREAKER_RECOVERY_TIMEOUT`: Recovery wait time in seconds (default: 60)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: JSON or text (default: json)

**Status**: Create new

---

### Database Layer

#### `app/database/__init__.py`
- Empty init file
- **Status**: Create new

#### `app/database/connection.py` (~50 lines)
**Purpose**: Database connection and session factory

**Contents**:
- Create SQLAlchemy async engine with asyncpg driver
- Session factory (AsyncSessionLocal)
- `get_db()` dependency function for FastAPI
- Context manager for database transactions
- Connection pooling configuration

**Key Code**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
```

**Status**: Create new

---

### Models & Schemas

#### `app/models/__init__.py`
- Empty init file
- **Status**: Create new

#### `app/models/user.py` (~60 lines)
**Purpose**: SQLAlchemy User ORM model

**Contents**:
- User table with columns: id, username, email, password_hash, is_active, is_locked, failed_login_attempts, locked_until, created_at, updated_at, last_login_at
- Constraints: unique username, unique email
- Indexes on username and email for fast lookup
- Methods: verify password (constant-time comparison)

**Key Code**:
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_email', 'email'),
    )
```

**Status**: Create new

#### `app/schemas/__init__.py`
- Empty init file
- **Status**: Create new

#### `app/schemas/user.py` (~100 lines)
**Purpose**: Pydantic request/response schemas

**Schemas**:

**RegisterRequest**:
- username (str, 3-32 chars, alphanumeric + underscore)
- email (str, valid email)
- password (str, min 8 chars, uppercase + lowercase + digit + special char)

**RegisterResponse**:
- id (int)
- username (str)
- email (str)
- created_at (datetime)

**LoginRequest**:
- username_or_email (str)
- password (str)

**LoginResponse**:
- access_token (str)
- refresh_token (str, for future use)
- token_type (str = "bearer")
- expires_in (int, seconds)

**Key Code**:
```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric + underscore')
        return v

    @field_validator('password')
    def password_complex(cls, v):
        if not (any(c.isupper() for c in v) and
                any(c.islower() for c in v) and
                any(c.isdigit() for c in v) and
                any(c in '!@#$%^&*' for c in v)):
            raise ValueError('Password must have uppercase, lowercase, digit, special char')
        return v

class RegisterResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
```

**Status**: Create new

---

### Exception Handling

#### `app/handlers/__init__.py`
- Empty init file
- **Status**: Create new

#### `app/handlers/exceptions.py` (~100 lines)
**Purpose**: Custom exceptions and exception handlers

**Custom Exceptions**:
```python
class AuthServiceException(Exception):
    """Base exception for auth service"""
    def __init__(self, detail: str, error_code: str, status_code: int = 500):
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code

class AuthenticationError(AuthServiceException):
    """Failed authentication attempt"""
    def __init__(self, detail="Invalid credentials"):
        super().__init__(detail, "AUTH_001", 401)

class UserAlreadyExistsError(AuthServiceException):
    """User already registered"""
    def __init__(self, detail="Email or username already exists"):
        super().__init__(detail, "AUTH_002", 409)

class ValidationError(AuthServiceException):
    """Invalid input validation"""
    def __init__(self, detail="Validation failed"):
        super().__init__(detail, "AUTH_003", 422)

class AccountLockedError(AuthServiceException):
    """Account is locked due to too many failed attempts"""
    def __init__(self, detail="Account is locked"):
        super().__init__(detail, "AUTH_004", 403)

class CircuitBreakerOpenError(AuthServiceException):
    """External service is unavailable"""
    def __init__(self, detail="Service temporarily unavailable"):
        super().__init__(detail, "SERVICE_001", 503)
```

**Exception Handlers**:
- Global exception handler that catches all custom exceptions
- Returns JSON response with: detail, error_code, timestamp, request_id
- Logs exception with full stack trace

**Key Code**:
```python
from fastapi.responses import JSONResponse
from fastapi import Request
from datetime import datetime
import uuid

async def auth_exception_handler(request: Request, exc: AuthServiceException):
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    )

def setup_exception_handlers(app):
    app.add_exception_handler(AuthServiceException, auth_exception_handler)
```

**Status**: Create new

---

### Services & Business Logic

#### `app/services/__init__.py`
- Empty init file
- **Status**: Create new

#### `app/services/auth_service.py` (~180 lines)
**Purpose**: Core authentication business logic

**AuthService Class**:

**Methods**:

1. **`register_user(username, email, password)`**
   - Validate input (use schemas)
   - Check if email/username already exists
   - Hash password using bcrypt
   - Create and save user to database
   - Return RegisterResponse
   - Raises: `UserAlreadyExistsError`, `ValidationError`

2. **`authenticate_user(username_or_email, password)`**
   - Find user by username or email
   - Check if account is locked
   - Check if locked_until has passed
   - Verify password hash using bcrypt constant-time comparison
   - If valid: reset failed_login_attempts, update last_login_at, return LoginResponse
   - If invalid: increment failed_login_attempts, lock if >= MAX_LOGIN_ATTEMPTS
   - Raises: `AuthenticationError`, `AccountLockedError`

3. **`_hash_password(password)`** (private)
   - Use bcrypt with cost factor 12
   - Return hashed password

4. **`_verify_password(plain_password, hashed_password)`** (private)
   - Use constant-time comparison (bcrypt.checkpw)
   - Return boolean

5. **`_generate_jwt_tokens(user_id, username)`** (private)
   - Generate access token with 30-minute expiry
   - Generate refresh token (for future use)
   - Return both tokens

**Key Code**:
```python
from app.utils.security import hash_password, verify_password, create_access_token
from app.handlers.exceptions import AuthenticationError, UserAlreadyExistsError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, username: str, email: str, password: str):
        # Check if user exists
        user = await self.db.execute(
            select(User).where(
                (User.email == email) | (User.username == username)
            )
        )
        if user.scalar_one_or_none():
            raise UserAlreadyExistsError()

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = User(username=username, email=email, password_hash=password_hash)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("User registered", extra={"user_id": user.id, "username": username})
        return RegisterResponse.from_orm(user)

    async def authenticate_user(self, username_or_email: str, password: str):
        # Find user
        user = await self.db.execute(
            select(User).where(
                (User.username == username_or_email) | (User.email == username_or_email)
            )
        )
        user = user.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            logger.warning("Failed login attempt", extra={"input": username_or_email})
            raise AuthenticationError()

        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                raise AccountLockedError()
            else:
                # Unlock account
                user.is_locked = False
                user.failed_login_attempts = 0

        # Success
        user.last_login_at = datetime.utcnow()
        user.failed_login_attempts = 0
        await self.db.commit()

        tokens = self._generate_jwt_tokens(user.id, user.username)
        logger.info("User login successful", extra={"user_id": user.id})
        return LoginResponse(**tokens)
```

**Status**: Create new

#### `app/services/circuit_breaker.py` (~120 lines)
**Purpose**: Circuit breaker pattern implementation

**CircuitBreaker Class**:

**States**:
- `CLOSED`: Normal operation, requests pass through
- `OPEN`: Service is failing, requests rejected immediately
- `HALF_OPEN`: Testing if service recovered

**Attributes**:
- `state`: Current state (enum)
- `failure_count`: Consecutive failures
- `success_count`: Consecutive successes in HALF_OPEN
- `last_failure_time`: Timestamp of last failure
- `failure_threshold`: Failures before opening
- `recovery_timeout`: Time before trying HALF_OPEN
- `success_threshold`: Successes to transition to CLOSED

**Methods**:

1. **`async call(func, *args, **kwargs)`**
   - Check current state
   - If CLOSED: call func, track success/failure
   - If OPEN: check if timeout passed
     - If yes: transition to HALF_OPEN, call func
     - If no: raise CircuitBreakerOpenError
   - If HALF_OPEN: call func, count successes/failures
   - Return result or raise exception

2. **`_transition_to_open()`**
   - Set state to OPEN
   - Record last_failure_time
   - Log event

3. **`_transition_to_closed()`**
   - Set state to CLOSED
   - Reset counters
   - Log event

4. **`_transition_to_half_open()`**
   - Set state to HALF_OPEN
   - Reset counters
   - Log event

**Key Code**:
```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 success_threshold: int = 2):
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError()

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return False
        return datetime.utcnow() >= (
            self.last_failure_time + timedelta(seconds=self.recovery_timeout)
        )
```

**Status**: Create new

---

### API Routes

#### `app/routers/__init__.py`
- Empty init file
- **Status**: Create new

#### `app/routers/auth.py` (~80 lines)
**Purpose**: API route handlers for authentication

**Routes**:

1. **`POST /register`**
   - Accept RegisterRequest
   - Call AuthService.register_user()
   - Return RegisterResponse (201 Created)
   - Handle exceptions via global handlers

2. **`POST /login`**
   - Accept LoginRequest
   - Call AuthService.authenticate_user()
   - Return LoginResponse (200 OK)
   - Handle exceptions via global handlers

**Key Code**:
```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from app.services.auth_service import AuthService
from app.database.connection import get_db

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    service = AuthService(db)
    return await service.register_user(request.username, request.email, request.password)

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login user and get access token"""
    service = AuthService(db)
    return await service.authenticate_user(request.username_or_email, request.password)
```

**Swagger/OpenAPI**:
- Endpoints automatically documented by FastAPI
- Include examples in request/response bodies
- Accessible at `/docs` (Swagger UI) and `/redoc`

**Status**: Create new

---

### Middleware & Utilities

#### `app/middleware/__init__.py`
- Empty init file
- **Status**: Create new

#### `app/middleware/logging.py` (~70 lines)
**Purpose**: Request logging middleware

**LoggingMiddleware Class**:
- Inject unique request ID in request context
- Log request start (method, path, remote address)
- Measure request duration
- Log request completion (status code, duration)
- Include correlation ID for distributed tracing

**Key Code**:
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid
import time
import logging
import json

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.time()
        logger.info(
            "request_start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "remote_addr": request.client.host if request.client else "unknown"
            }
        )

        response = await call_next(request)

        duration = time.time() - start
        logger.info(
            "request_end",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration * 1000
            }
        )

        response.headers["X-Request-ID"] = request_id
        return response
```

**Status**: Create new

#### `app/utils/__init__.py`
- Empty init file
- **Status**: Create new

#### `app/utils/security.py` (~80 lines)
**Purpose**: Security utilities (password hashing, JWT tokens)

**Functions**:

1. **`hash_password(password: str) -> str`**
   - Use bcrypt with cost factor 12
   - Return hashed password

2. **`verify_password(plain_password: str, hashed_password: str) -> bool`**
   - Use bcrypt.checkpw for constant-time comparison
   - Return boolean

3. **`create_access_token(data: dict, expires_delta: timedelta = None) -> str`**
   - Create JWT token with standard claims (sub, exp, iat, jti)
   - Include user_id in 'sub' claim
   - Default expiry 30 minutes
   - Sign with SECRET_KEY using HS256

4. **`create_refresh_token(data: dict) -> str`** (for future use)
   - Create JWT token with longer expiry (7 days)

5. **`decode_token(token: str) -> dict`**
   - Decode JWT token
   - Verify signature and expiry
   - Return payload
   - Raise exception if invalid

**Key Code**:
```python
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from app.config import settings
from app.handlers.exceptions import AuthenticationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: int, username: str, expires_delta: timedelta = None) -> dict:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": expire
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {
        "access_token": token,
        "refresh_token": "",  # For future implementation
        "token_type": "bearer",
        "expires_in": int(expires_delta.total_seconds())
    }
```

**Status**: Create new

---

### Database Migrations

#### `migrations/` (Alembic setup)
**Purpose**: Database schema version control

**Files**:
- `alembic.ini`: Alembic configuration
- `env.py`: Alembic environment configuration for async
- `script.py.mako`: Migration template
- `versions/`: Migration files

#### `migrations/versions/001_initial.py`
**Purpose**: Initial schema with users table

**Contents**:
```python
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(32), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_locked', sa.Boolean(), default=False),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_username', 'users', ['username'])
    op.create_index('idx_email', 'users', ['email'])

def downgrade():
    op.drop_table('users')
```

**Status**: Create new

---

### Testing

#### `tests/__init__.py`
- Empty init file
- **Status**: Create new

#### `tests/conftest.py` (~100 lines)
**Purpose**: Pytest fixtures and test configuration

**Fixtures**:

1. **`test_db`**: In-memory database or test PostgreSQL
2. **`db_session`**: Database session with transaction rollback
3. **`client`**: FastAPI TestClient
4. **`test_user`**: Pre-created test user
5. **`test_user_credentials`**: Test user login credentials

**Key Code**:
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db
from app.models.user import User, Base
from app.utils.security import hash_password

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def test_db():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    async_session = async_sessionmaker(test_db, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest.fixture
def client(db_session):
    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def test_user_credentials():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!"
    }
```

**Status**: Create new

#### `tests/test_auth.py` (~150 lines)
**Purpose**: Integration tests for authentication endpoints

**Tests**:
- `test_register_success`: Valid registration
- `test_register_duplicate_email`: Email conflict
- `test_register_invalid_password`: Password too weak
- `test_login_success`: Valid login returns token
- `test_login_invalid_password`: Wrong password
- `test_login_user_not_found`: Non-existent user
- `test_swagger_docs`: Swagger UI accessible

**Status**: Create new

#### `tests/test_services.py` (~150 lines)
**Purpose**: Unit tests for business logic

**Tests**:
- `test_register_user_success`
- `test_register_duplicate_email`
- `test_authenticate_user_success`
- `test_authenticate_invalid_password`
- `test_failed_login_increments_counter`
- `test_account_locks_after_max_attempts`
- `test_locked_account_unlocks_after_timeout`

**Status**: Create new

#### `tests/test_circuit_breaker.py` (~100 lines)
**Purpose**: Unit tests for circuit breaker

**Tests**:
- `test_circuit_breaker_closed_state`
- `test_circuit_breaker_opens_after_failures`
- `test_circuit_breaker_half_open_after_timeout`
- `test_circuit_breaker_closes_on_success`
- `test_circuit_breaker_opens_again_on_failure`

**Status**: Create new

---

### Project Documentation

#### `README.md`
**Contents**:
- Project overview
- Tech stack
- Setup instructions (venv, requirements, migrations)
- Running the app and tests
- API documentation links
- Environment variables
- Project structure

**Status**: Create new

#### `.gitignore`
**Contents**:
- Python: `__pycache__`, `*.pyc`, `.venv`, `venv/`
- Environment: `.env`
- Testing: `.coverage`, `htmlcov/`
- IDE: `.vscode`, `.idea`
- Database: `*.db`, `*.sqlite`
- OS: `.DS_Store`, `*.log`

**Status**: Create new

---

## 3. Interfaces: APIs & Function Signatures

### REST API Endpoints

#### `POST /api/v1/auth/register`
**Request**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2026-02-19T10:00:00Z"
}
```

**Errors**:
- 409 Conflict: Email/username already exists
- 422 Unprocessable Entity: Invalid input

---

#### `POST /api/v1/auth/login`
**Request**:
```json
{
  "username_or_email": "john_doe",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors**:
- 401 Unauthorized: Invalid credentials or user not found
- 403 Forbidden: Account locked

---

#### `GET /health`
**Response** (200 OK):
```json
{
  "status": "healthy"
}
```

---

### Key Function Signatures

```python
# Authentication Service
async def register_user(username: str, email: str, password: str) -> RegisterResponse

async def authenticate_user(username_or_email: str, password: str) -> LoginResponse

# Security Utilities
def hash_password(password: str) -> str

def verify_password(plain_password: str, hashed_password: str) -> bool

def create_access_token(user_id: int, username: str, expires_delta: Optional[timedelta] = None) -> dict

def decode_token(token: str) -> dict

# Circuit Breaker
async def call(func: Callable, *args, **kwargs) -> Any
```

---

## 4. Trade-offs: Why This Approach

### Async-First Design
**Trade-off**: Complexity vs Performance
- **Pro**: Handles concurrent requests efficiently, better resource utilization
- **Con**: More complex code, requires async-aware libraries
- **Decision**: FastAPI's async support is mature; the performance benefits justify complexity

### Service Layer Abstraction
**Trade-off**: Code organization vs Direct DB access
- **Pro**: Better testability, reusable business logic, clear separation of concerns
- **Con**: Additional layer of indirection
- **Decision**: Maintainability and testability are worth the extra layer

### Bcrypt + Cost Factor 12
**Trade-off**: Security vs Performance
- **Pro**: Resistant to brute force, follows NIST recommendations
- **Con**: Slower hashing (intentional, ~100ms per hash)
- **Decision**: Security is critical for auth; performance is acceptable

### SQLAlchemy ORM
**Trade-off**: Type safety vs Query performance
- **Pro**: Type-safe, prevents SQL injection, async support
- **Con**: Slightly slower than raw SQL
- **Decision**: Security and maintainability outweigh marginal performance cost

### Centralized Exception Handling
**Trade-off**: Consistency vs Granular control
- **Pro**: Consistent error responses, single place to modify format
- **Con**: Less granular control over specific error responses
- **Decision**: Consistency and maintainability are more important

### JWT Tokens without Refresh Token Rotation
**Trade-off**: Security vs Simplicity
- **Pro**: Simple implementation for Phase 1
- **Con**: Compromised token valid until expiry
- **Decision**: Phase 1 focus on core functionality; refresh rotation in Phase 2

### In-Memory Test Database
**Trade-off**: Test isolation vs Real environment
- **Pro**: Fast tests, no external dependencies
- **Con**: Doesn't test actual PostgreSQL behaviors (specific SQL features)
- **Decision**: Most logic is database-agnostic; can test with PostgreSQL in CI/CD if needed

---

## 5. Open Questions for Implementation

1. **Should we implement email verification in Phase 1?**
   - Current design allows for it but doesn't require it
   - Could use circuit breaker for email service

2. **JWT token storage strategy?**
   - Currently planning httpOnly cookies (for web clients)
   - Mobile clients would store in secure storage
   - Should we document both approaches?

3. **Rate limiting scope?**
   - Current design: per user (by username/email)
   - Should we also limit by IP address?

4. **Logging storage?**
   - Current design: stdout (stdout-based with JSON format)
   - Should we pre-configure file logging paths?

5. **Database connection pooling settings?**
   - Current: pool_size=20, max_overflow=0
   - Should these be configurable?

---

## 6. Implementation Order (Recommended)

1. **Setup** (requirements.txt, .env.example, config.py)
2. **Database** (models/user.py, database/connection.py, migrations)
3. **Security** (utils/security.py)
4. **Exceptions** (handlers/exceptions.py)
5. **Services** (services/auth_service.py, services/circuit_breaker.py)
6. **Routes** (routers/auth.py)
7. **Middleware** (middleware/logging.py)
8. **Main App** (app/main.py)
9. **Testing** (tests/)
10. **Documentation** (README.md)

---

**Document Status**: ✅ Ready for Implementation Phase
**Created**: 2026-02-19
**Version**: 1.0
