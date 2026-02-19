# Implementation Guide: FastAPI Auth Service

## Overview

This guide provides step-by-step instructions for implementing the FastAPI authentication service based on the analysis findings.

---

## Phase 1: Exception & Logging Infrastructure (2-3 hours)

### 1.1 Create Exception Hierarchy
**File**: `app/utils/exceptions.py`

**Purpose**: Define all custom exceptions used throughout the application

**Key Classes**:
```python
class AppException(Exception):
    """Base exception for all application errors"""
    - Should include error_code, detail, status_code

class AuthException(AppException):
    """Base for authentication errors"""

class InvalidCredentialsException(AuthException):
    """Login failed (email/password invalid)"""

class UserAlreadyExistsException(AuthException):
    """Duplicate user (email or username exists)"""

class TokenExpiredException(AuthException):
    """JWT token has expired"""

class ValidationException(AppException):
    """Input validation failed"""

class DatabaseException(AppException):
    """Database operation failed"""

class CircuitBreakerOpenException(AppException):
    """Circuit breaker is open (service unavailable)"""
```

**Best Practices**:
- Each exception should have `error_code`, `detail`, and `status_code`
- Generic messages for auth failures (don't reveal if user exists)
- Include request_id in exception if available
- Use enum for error codes (e.g., INVALID_CREDENTIALS, USER_EXISTS)

**Testing**:
- Create test file: `tests/unit/test_exceptions.py`
- Verify each exception can be instantiated
- Verify error_code and status_code mapping

---

### 1.2 Create Structured Logging
**File**: `app/utils/logger.py`

**Purpose**: Centralized logging with structured JSON output

**Key Functions**:
```python
def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance"""

def setup_logging(log_level: str = "INFO") -> None:
    """Initialize logging system"""

class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON output"""
    - Include timestamp, level, message, context
    - Include request_id if available (via contextvars)

def get_request_id() -> str:
    """Get current request ID from context"""

def set_request_id(request_id: str) -> None:
    """Set request ID in context (called by middleware)"""
```

**Best Practices**:
- Use contextvars for request ID (thread-safe with async)
- Format timestamps in ISO 8601 (e.g., "2024-01-15T10:30:45.123Z")
- Include all relevant context (user_id, endpoint, method, etc.)
- Exclude passwords, tokens, sensitive data
- Different log level for health checks vs regular operations

**Testing**:
- Create test file: `tests/unit/test_logger.py`
- Verify JSON format
- Verify request ID propagation
- Mock logger in other tests

---

### 1.3 Create Exception Handler Middleware
**File**: `app/middleware/exception.py`

**Purpose**: Global exception handler that catches all errors and returns consistent response

**Key Class**:
```python
class ExceptionHandlerMiddleware:
    """Middleware to catch and handle all exceptions"""

    async def __call__(self, scope, receive, send):
        # Wrap endpoint call in try/except
        # Catch all exceptions
        # Convert to consistent error response format
        # Return JSON error with proper status code
        # Log error with context
```

**Response Format**:
```json
{
    "detail": "Invalid credentials",
    "error_code": "INVALID_CREDENTIALS",
    "timestamp": "2024-01-15T10:30:45.123Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Best Practices**:
- Handle all exception types (custom + built-in)
- Map exceptions to HTTP status codes
- Never include stack traces in response
- Log full error with context
- Return 500 for unhandled exceptions (not 500 with details)
- Exclude certain paths from detailed error handling (/health, /docs)

**Testing**:
- Create test file: `tests/integration/test_exception_handling.py`
- Test each exception type
- Verify error response format
- Verify correct HTTP status codes

---

### 1.4 Create Request Logging Middleware
**File**: `app/middleware/logging.py`

**Purpose**: Log all HTTP requests/responses with request ID

**Key Class**:
```python
class RequestLoggingMiddleware:
    """Middleware to log requests and responses"""

    async def __call__(self, scope, receive, send):
        # Generate request ID (UUID)
        # Store in context (contextvars)
        # Log request: method, path, headers, query params
        # Measure response time
        # Log response: status code, response time
        # Exclude health, swagger endpoints from detailed logging
```

**Log Entry Example**:
```json
{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "level": "INFO",
    "message": "POST /auth/login",
    "method": "POST",
    "path": "/auth/login",
    "status_code": 200,
    "duration_ms": 145
}
```

**Best Practices**:
- Use UUID4 for request ID (fully random, no guessing)
- Store in contextvars (per-request storage)
- Measure response time accurately
- Exclude non-business endpoints (/health, /docs, /redoc, /openapi.json)
- Sanitize query params (remove secrets)
- Don't log request body (contains passwords)
- Include user_id if authenticated

**Testing**:
- Create test file: `tests/integration/test_logging_middleware.py`
- Verify request ID generation
- Verify request ID in logs
- Verify response time calculation
- Verify health endpoint excluded

---

### 1.5 Update app/middleware/__init__.py
Create empty `__init__.py` file to make middleware a package.

---

### 1.6 Update app/utils/__init__.py
Create empty `__init__.py` file to make utils a package.

---

## Phase 2: Authentication Utilities (2-3 hours)

### 2.1 Create Password Utility
**File**: `app/utils/password.py`

**Purpose**: Bcrypt password hashing and verification

**Key Functions**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """Hash plain password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

**Best Practices**:
- Use bcrypt default work factor (12)
- passlib handles timing attacks
- Never store plain passwords
- Hash verification always returns bool
- Hashes are always different (salting)

**Testing** (`tests/unit/test_password_utils.py`):
- Hash generates different output each time (salting)
- Valid password verifies
- Invalid password fails
- Hash never equals plain password
- Long passwords handled
- Special characters handled

---

### 2.2 Create JWT Utility
**File**: `app/utils/jwt.py`

**Purpose**: JWT token creation and validation

**Key Functions**:
```python
from jose import JWTError, jwt
from datetime import datetime, timedelta

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    # Default expiration: 30 minutes
    # Payload: {"sub": user_id, "exp": expiration}

def create_refresh_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    # Default expiration: 7 days
    # Payload: {"sub": user_id, "exp": expiration, "type": "refresh"}

def verify_token(token: str) -> dict:
    """Decode and validate JWT token"""
    # Decode using JWT_SECRET_KEY
    # Validate not expired
    # Raise TokenExpiredException if expired
    # Raise InvalidTokenException if invalid

def extract_user_id_from_token(token: str) -> int:
    """Extract user_id from token"""
    # Use verify_token
    # Return user_id from "sub" claim
```

**Best Practices**:
- Use HS256 algorithm (symmetric, shared secret)
- Include expiration ("exp" claim)
- Include user ID in "sub" claim
- Separate access and refresh tokens
- Include token "type" in refresh token
- Proper error handling for expired/invalid tokens
- Use UTC timezone

**Configuration**:
```python
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
```

**Testing** (`tests/unit/test_jwt_utils.py`):
- Create access token with default expiration
- Create access token with custom expiration
- Create refresh token with default expiration
- Verify valid token succeeds
- Verify expired token raises exception
- Verify invalid token raises exception
- Extract user_id from valid token
- Extract from invalid token raises exception
- Token with tampered payload fails

---

### 2.3 Create Circuit Breaker Utility
**File**: `app/utils/circuit_breaker.py`

**Purpose**: Resilience pattern to prevent cascading failures

**Key Class**:
```python
from enum import Enum
import time
import threading

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
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
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        # Check state
        # If OPEN and not timed out, raise CircuitBreakerOpenException
        # If OPEN and timed out, transition to HALF_OPEN
        # If HALF_OPEN, allow one call and track result
        # Execute function, catch expected_exception
        # On failure: increment count, transition to OPEN if threshold reached
        # On success: reset count, transition to CLOSED

    def transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN after timeout"""

    def transition_to_closed(self):
        """Reset circuit to CLOSED on success"""

    def transition_to_open(self):
        """Transition to OPEN on failure threshold reached"""

    def __enter__(self):
        """Context manager support"""

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
```

**Best Practices**:
- Thread-safe state transitions (use threading.Lock)
- Clear state documentation
- Logging on state changes
- Exponential backoff optional (not required)
- Half-open allows single request to test recovery
- Reset on successful request

**Testing** (`tests/unit/test_circuit_breaker.py`):
- Initial state is CLOSED
- CLOSED state allows all requests
- Transition to OPEN after threshold
- OPEN state rejects requests
- Transition to HALF_OPEN after timeout
- HALF_OPEN allows one request
- HALF_OPEN→CLOSED on success
- HALF_OPEN→OPEN on failure
- Track failure counts
- Manual reset function

---

## Phase 3: Services & Dependencies (2-3 hours)

### 3.1 Create User Service
**File**: `app/services/user_service.py`

**Purpose**: User data management

**Key Functions**:
```python
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID from database"""
        # Use select() with where(User.id == user_id)
        # Handle not found gracefully

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email from database"""
        # Use select() with where(User.email == email)
        # Case-sensitive lookup

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username from database"""
        # Use select() with where(User.username == username)
        # Case-sensitive lookup

    async def create_user(
        self,
        username: str,
        email: str,
        hashed_password: str
    ) -> User:
        """Create new user"""
        # Check if user exists first (optional, DB will enforce)
        # Create User object
        # Add to session
        # Commit
        # Return created user
        # Handle unique constraint violation → UserAlreadyExistsException
```

**Best Practices**:
- Always use async/await with database
- Use try/except for constraint violations
- Return None for not found (not exceptions)
- Proper async session usage
- Logging for all operations
- Case-sensitive lookups for username/email

**Testing** (`tests/unit/test_user_service.py`):
- Get existing user by ID
- Get existing user by email
- Get existing user by username
- Not found returns None
- Create user successfully
- Create duplicate user raises exception
- Concurrent creates handled

---

### 3.2 Create Auth Service
**File**: `app/services/auth_service.py`

**Purpose**: Authentication business logic

**Key Functions**:
```python
class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        session: AsyncSession
    ) -> TokenResponse:
        """Register new user"""
        # Check if user already exists (email or username)
        # Hash password
        # Create user via user_service
        # Generate tokens
        # Return TokenResponse with user and tokens

    async def login(
        self,
        email_or_username: str,
        password: str,
        session: AsyncSession
    ) -> TokenResponse:
        """Login user"""
        # Get user by email or username
        # If not found → InvalidCredentialsException
        # If not active → InvalidCredentialsException (generic)
        # Verify password
        # If invalid → InvalidCredentialsException
        # Update last_login timestamp
        # Generate tokens
        # Return TokenResponse

    async def refresh_access_token(
        self,
        refresh_token: str,
        session: AsyncSession
    ) -> TokenResponse:
        """Generate new access token from refresh token"""
        # Verify refresh token
        # Extract user_id
        # Get user from database
        # Generate new access token
        # Return TokenResponse (with new access token, same refresh token)
```

**Best Practices**:
- Never reveal if user exists (all auth failures → same message)
- Check is_active flag
- Update last_login on successful login
- Generate both tokens on register/login
- On refresh, generate new access token (optional: rotate refresh token)
- Use UserService for data access
- Logging for all operations (without sensitive data)

**Testing** (`tests/unit/test_auth_service.py`):
- Register with valid data
- Register duplicate email
- Register duplicate username
- Login with email
- Login with username
- Login invalid credentials
- Login user inactive
- Refresh token success
- Refresh invalid token

---

### 3.3 Create Dependency Injection
**File**: `app/dependencies.py`

**Purpose**: FastAPI dependency injection setup

**Key Functions**:
```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency"""
    # Use AsyncSessionLocal from database.py
    # Yield session
    # Cleanup on exit (context manager)

async def get_current_user(
    token: str = Header(..., alias="Authorization"),
    session: AsyncSession = Depends(get_db_session)
) -> User:
    """Get current user from JWT token"""
    # Extract token from "Bearer <token>"
    # Verify token
    # Extract user_id
    # Get user from database
    # Check is_active
    # Return User object
    # Raise HTTPException on invalid/expired token

def get_logger() -> logging.Logger:
    """Get logger instance"""
    # Return logger for routes
    # Allows DI of logger

def get_request_id() -> str:
    """Get current request ID from context"""
    # From contextvars
    # Used by routes if needed
```

**Best Practices**:
- get_db_session provides session for all routes
- get_current_user validates token and returns user
- Use HTTPException for missing/invalid token (returns 401)
- All exceptions caught by middleware
- Type hints for all parameters
- Return types specified

**Testing**:
- Unit test each dependency (mock dependencies)
- Integration test in route tests
- Verify exceptions raised correctly

---

### 3.4 Create app/services/__init__.py
Empty init file to make services a package.

---

## Phase 4: Routes & Application (2 hours)

### 4.1 Create Auth Routes
**File**: `app/routes/auth.py`

**Purpose**: Authentication HTTP endpoints

**Key Endpoints**:
```python
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_db_session),
    logger: logging.Logger = Depends(get_logger)
) -> TokenResponse:
    """Register new user

    - **email**: Unique email address
    - **username**: Unique username
    - **password**: Password (min 8 chars)

    Returns TokenResponse with access/refresh tokens
    """
    # Create auth service
    # Call register_user
    # Log successful registration
    # Return token response

@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_db_session),
    logger: logging.Logger = Depends(get_logger)
) -> TokenResponse:
    """Login user

    - **email** OR **username**: Either email or username
    - **password**: User password

    Returns TokenResponse with access/refresh tokens
    """
    # Validate email or username provided
    # Create auth service
    # Call login
    # Log successful login
    # Return token response

@router.post("/refresh", response_model=TokenResponse, status_code=200)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    logger: logging.Logger = Depends(get_logger)
) -> TokenResponse:
    """Refresh access token

    - **refresh_token**: Valid refresh token

    Returns TokenResponse with new access token
    """
    # Create auth service
    # Call refresh_access_token
    # Log token refresh
    # Return token response
```

**Best Practices**:
- Use APIRouter for modular routing
- Use response_model for auto validation
- Use status_code for correct HTTP status
- Docstrings with request/response details
- Use Depends() for DI
- Exceptions raised by services caught by middleware
- Log all operations without sensitive data

**Error Handling**:
- ValidationException (400) - Bad input
- UserAlreadyExistsException (409) - Duplicate user
- InvalidCredentialsException (401) - Login failed
- TokenExpiredException (401) - Refresh failed
- All others caught by middleware

**Testing** (`tests/integration/test_auth_routes.py`):
- POST /auth/register success (201)
- POST /auth/register validation error (400)
- POST /auth/register duplicate (409)
- POST /auth/login success (200)
- POST /auth/login invalid credentials (401)
- POST /auth/login user inactive (401)
- POST /auth/login missing credentials (400)
- POST /auth/refresh success (200)
- POST /auth/refresh invalid token (401)
- POST /auth/refresh expired token (401)
- Response format validation

---

### 4.2 Create Health Route
**File**: `app/routes/health.py`

**Purpose**: Health check endpoint for monitoring

**Key Endpoint**:
```python
router = APIRouter(tags=["health"])

@router.get("/health", status_code=200)
async def health_check() -> dict:
    """Health check endpoint

    Returns basic health status for load balancers/monitoring
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Best Practices**:
- Simple, fast endpoint
- Excluded from detailed logging
- Returns JSON (not plain text)
- Status code 200

**Testing** (`tests/integration/test_health_route.py`):
- GET /health returns 200
- Response has status field

---

### 4.3 Create app/routes/__init__.py
Empty init file to make routes a package.

---

### 4.4 Create FastAPI Application
**File**: `app/main.py`

**Purpose**: FastAPI app initialization and configuration

**Key Setup**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Auth Service",
    description="FastAPI authentication service",
    version="1.0.0"
)

# Middleware registration (order matters!)
app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or settings.CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Route registration
app.include_router(auth_router, prefix="/auth")
app.include_router(health_router)

# Startup event
@app.on_event("startup")
async def startup():
    """Initialize database tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown"""
    await engine.dispose()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Auth Service API"}
```

**Middleware Order** (Important!):
1. ExceptionHandlerMiddleware (catches all exceptions)
2. RequestLoggingMiddleware (logs requests)
3. CORSMiddleware (CORS handling)
4. (Other custom middleware as needed)

**Best Practices**:
- Title, description, version for Swagger
- Middleware order matters (exception handler first)
- CORS configured properly
- Database initialization on startup
- Cleanup on shutdown
- Automatic Swagger at /docs
- Automatic ReDoc at /redoc

**Testing** (`tests/integration/test_swagger.py`):
- GET /docs returns Swagger UI
- GET /redoc returns ReDoc
- GET /openapi.json returns valid schema

---

### 4.5 Update Configuration
**File**: `app/config.py`

**Changes**:
- Add CORS_ORIGINS setting
- Add API_TITLE, API_DESCRIPTION, API_VERSION
- Keep existing auth and DB settings

```python
class Settings(BaseSettings):
    # ... existing ...

    # API Configuration
    API_TITLE: str = "Auth Service"
    API_DESCRIPTION: str = "FastAPI authentication service"
    API_VERSION: str = "1.0.0"

    # CORS Configuration
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]

    # Additional settings
    ALLOW_CREDENTIALS: bool = True
    REQUEST_ID_HEADER: str = "X-Request-ID"
```

---

### 4.6 Update Database Initialization
**File**: `app/database.py`

**Changes**:
- Add table initialization function

```python
async def init_db():
    """Create all tables in database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database connection"""
    await engine.dispose()
```

---

## Phase 5: Testing (2 hours)

### 5.1 Create Test Fixtures
**File**: `tests/conftest.py`

**Purpose**: Shared fixtures for all tests

**Key Fixtures**:
```python
@pytest.fixture
def test_db():
    """Create test database"""
    # Use in-memory SQLite
    # Create all tables
    # Yield session
    # Cleanup after

@pytest.fixture
async def client(test_db):
    """Create FastAPI test client"""
    # Create TestClient with test app
    # Override get_db_session
    # Yield client

@pytest.fixture
async def test_user(test_db):
    """Create test user in database"""
    # Hash password
    # Create user
    # Commit
    # Yield user

@pytest.fixture
async def test_tokens(test_user):
    """Create test JWT tokens"""
    # Create access token
    # Create refresh token
    # Yield both tokens

@pytest.fixture
def auth_headers(test_tokens):
    """Create authorization header"""
    return {"Authorization": f"Bearer {test_tokens['access_token']}"}
```

**Best Practices**:
- Use in-memory SQLite for speed
- Fixtures are functions with yield
- Cleanup happens after yield
- Async fixtures with async def
- pytest-asyncio for async support

---

### 5.2 Create Unit Tests
Follow the test files listed in Phase 1-2 sections above.

**Key Testing Tools**:
- `pytest` - Test runner
- `pytest-asyncio` - Async support
- `pytest-cov` - Coverage reporting
- Fixtures - Reusable test setup
- Mock/patch - Override dependencies

**Test Structure**:
```python
class TestClassName:
    @pytest.mark.asyncio
    async def test_function_name(self, fixture_name):
        # Arrange
        # Act
        # Assert
```

---

### 5.3 Create Integration Tests
**File**: `tests/integration/test_auth_routes.py`

**Test Examples**:
```python
@pytest.mark.asyncio
async def test_register_success(client, test_db):
    """Test successful user registration"""
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "test_password"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "INVALID_CREDENTIALS"
```

---

## Phase 6: Validation & Optimization (1 hour)

### 6.1 Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_password_utils.py -v

# Run integration tests only
pytest tests/integration/ -v
```

### 6.2 Coverage Goals
- **Target**: 85%+ overall coverage
- **Critical paths**: 95%+ (auth, password, jwt, exceptions)
- **Non-critical**: 80%+ (routes, services, middleware)

### 6.3 Manual Testing
```bash
# Start server
uvicorn app.main:app --reload

# In another terminal, test endpoints:

# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Swagger UI
open http://localhost:8000/docs
```

### 6.4 Security Review
- [ ] No passwords in logs
- [ ] No tokens in logs
- [ ] Error messages don't reveal user existence
- [ ] Bcrypt hashing used correctly
- [ ] JWT tokens validated properly
- [ ] CORS configured appropriately
- [ ] Database connections handled safely
- [ ] No SQL injection vulnerabilities
- [ ] No XXE vulnerabilities
- [ ] Request validation on all endpoints

### 6.5 Performance Checklist
- [ ] Database queries are fast
- [ ] No N+1 query problems
- [ ] Connection pooling working
- [ ] Response times < 100ms (excluding cold starts)
- [ ] Memory usage stable under load
- [ ] No memory leaks in async code

---

## Key Implementation Principles

### 1. Always Use Async
- All database operations async
- All middleware async
- No blocking calls in FastAPI
- Use `await` for all async functions

### 2. Never Log Sensitive Data
- Password field always redacted
- Token field always redacted
- Email may be included (less sensitive)
- User ID safe to log

### 3. Security-First Error Messages
- "Invalid credentials" for both invalid email and password
- Never say "user not found"
- Never say "user already exists" in 400 response (use 409)
- All auth errors return 401 (except validation errors)

### 4. Dependency Injection
- Use FastAPI's `Depends()` for all dependencies
- Keep functions pure (no side effects)
- Mock dependencies in tests

### 5. Proper Async Context Managers
```python
# Right way
async with AsyncSessionLocal() as session:
    await session.execute(...)

# Wrong way
session = AsyncSessionLocal()
await session.execute(...)
# Might not cleanup on exception
```

### 6. Type Hints Everywhere
```python
# Right way
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_db_session)
) -> TokenResponse:

# Wrong way
async def login(credentials, session):
```

---

## Common Pitfalls to Avoid

1. **Forgetting `await` in async code**
   - Every async function call needs `await`

2. **Not using context managers for sessions**
   - Always `async with AsyncSessionLocal() as session:`

3. **Logging sensitive data**
   - Never log passwords or tokens
   - Sanitize request bodies

4. **Incorrect exception handling**
   - Let custom exceptions bubble up to middleware
   - Don't catch and re-raise without changes

5. **Not testing async code properly**
   - Use `@pytest.mark.asyncio` decorator
   - Use `pytest-asyncio` plugin

6. **Middleware ordering**
   - Exception handler must be first
   - Order matters for middleware chain

7. **Not validating input**
   - Always use Pydantic schemas
   - FastAPI validates automatically

8. **Forgetting to close resources**
   - Database connections must close
   - Files must close
   - Use context managers

---

## Debugging Tips

### View Full Error Traceback
```python
# In pytest
pytest -vv --tb=long

# Set log level to DEBUG
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Debug Async Code
```python
# Add async debugging
import asyncio
asyncio.set_debug(True)

# Or use pytest with print statements
pytest -s -vv
```

### Check Database
```bash
# SQLite CLI
sqlite3 test.db

# View schema
.schema users

# Query users
SELECT * FROM users;
```

### Test Individual Functions
```python
# pytest allows running single tests
pytest tests/unit/test_password_utils.py::test_hash_password -v

# With output
pytest -s -vv tests/unit/test_password_utils.py::test_hash_password
```

---

## File Checklist

After completion, verify all files exist:

### Source Code (17 files)
- [ ] app/utils/__init__.py
- [ ] app/utils/exceptions.py
- [ ] app/utils/logger.py
- [ ] app/utils/password.py
- [ ] app/utils/jwt.py
- [ ] app/utils/circuit_breaker.py
- [ ] app/middleware/__init__.py
- [ ] app/middleware/exception.py
- [ ] app/middleware/logging.py
- [ ] app/services/__init__.py
- [ ] app/services/user_service.py
- [ ] app/services/auth_service.py
- [ ] app/routes/__init__.py
- [ ] app/routes/auth.py
- [ ] app/routes/health.py
- [ ] app/dependencies.py
- [ ] app/main.py

### Modified Files (2 files)
- [ ] app/config.py (updated)
- [ ] app/database.py (updated)
- [ ] app/models/schemas.py (updated if needed)

### Test Files (10 files)
- [ ] tests/__init__.py
- [ ] tests/conftest.py
- [ ] tests/fixtures/__init__.py
- [ ] tests/fixtures/database.py
- [ ] tests/unit/__init__.py
- [ ] tests/unit/test_password_utils.py
- [ ] tests/unit/test_jwt_utils.py
- [ ] tests/unit/test_exceptions.py
- [ ] tests/unit/test_circuit_breaker.py
- [ ] tests/unit/test_user_service.py
- [ ] tests/unit/test_auth_service.py
- [ ] tests/integration/__init__.py
- [ ] tests/integration/test_auth_routes.py
- [ ] tests/integration/test_health_route.py
- [ ] tests/integration/test_middleware.py
- [ ] tests/integration/test_swagger.py

---

This implementation guide provides everything needed to build a complete, well-tested FastAPI authentication service with all required features.
