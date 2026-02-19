# Auth System Design

## Approach

This design implements a **production-ready, stateless JWT-based authentication system** with comprehensive logging, centralized exception handling, and circuit breaker fault tolerance. The architecture follows FastAPI best practices with clear separation of concerns:

- **API Layer**: FastAPI routes with Pydantic validation
- **Service Layer**: Business logic (auth, user management)
- **Data Layer**: SQLAlchemy ORM with async sessions
- **Cross-cutting Concerns**: Logging, exception handling, circuit breaker
- **Testing**: Comprehensive unit and integration tests with mocked dependencies

Key design decisions:
1. **Stateless JWT Authentication**: No session storage required, scalable across multiple instances
2. **Async Throughout**: All database operations are async for high concurrency
3. **Dependency Injection**: Clean testability through FastAPI's `Depends()` pattern
4. **Structured Logging**: JSON format for easy parsing and centralized log aggregation
5. **Consistent Error Responses**: Standardized error format with error codes and request IDs
6. **Circuit Breaker Pattern**: Graceful degradation on database/external service failures

---

## Detailed Changes

### 1. Configuration Management

**File**: `app/config.py`

```python
# Loads environment variables via pydantic-settings
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./test.db"
    JWT_SECRET_KEY: str  # Min 32 characters
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"  # development, testing, production
    LOG_LEVEL: str = "INFO"
    DATABASE_MAX_POOL_SIZE: int = 20
    CIRCUIT_BREAKER_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS: int = 1
```

**What it does**:
- Centralizes all configuration in one place
- Supports .env file loading
- Validates required fields at startup
- Provides sensible defaults for non-critical settings

---

### 2. Database Connection Management

**File**: `app/database.py`

```python
# Creates async SQLAlchemy engine and session factory
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_size=settings.DATABASE_MAX_POOL_SIZE,
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

**What it does**:
- Configures async database engine with connection pooling
- Provides async session context manager
- Exports Base class for model inheritance
- Supports SQLite development and PostgreSQL production

---

### 3. User ORM Model

**File**: `app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True)
    username: str = Column(String(50), unique=True, nullable=False, index=True)
    email: str = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password: str = Column(String(255), nullable=False)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Optional[datetime] = Column(DateTime, nullable=True)
```

**What it does**:
- Stores user account data with proper constraints
- Indexes on email/username for fast lookups
- Tracks creation, update, and last login times
- Uses hashed passwords (never plaintext)

---

### 4. Pydantic Schemas

**File**: `app/models/schemas.py`

```python
class UserRegister(BaseModel):
    email: EmailStr  # Validates email format
    username: str    # Alphanumeric, 3-50 chars
    password: str    # Min 12 chars, complexity rules

class UserLogin(BaseModel):
    email: Optional[str] = None  # Or use username
    username: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
```

**What it does**:
- Validates API request/response data
- Separates API concerns from ORM models
- Provides clear contracts for API consumers

---

### 5. JWT Utilities

**File**: `app/utils/jwt.py`

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # Creates JWT with configurable expiration
    # Payload includes user_id and other claims

def create_refresh_token(data: dict) -> str:
    # Creates longer-lived refresh token

def decode_token(token: str) -> dict:
    # Validates JWT signature
    # Checks expiration
    # Returns decoded payload or raises TokenInvalidException
```

**What it does**:
- Creates and validates JWT tokens
- Separates access tokens (short-lived) from refresh tokens (long-lived)
- Handles token expiration and signature validation
- Raises appropriate exceptions for error cases

---

### 6. Password Utilities

**File**: `app/utils/password.py`

```python
def hash_password(password: str) -> str:
    # Uses bcrypt algorithm with salt
    # Returns hashed password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Safely compares plaintext with hash
    # Returns True if valid, False otherwise
    # Prevents timing attacks
```

**What it does**:
- Hashes passwords using bcrypt (slow, secure algorithm)
- Verifies plaintext against hash
- Prevents plaintext password storage

---

### 7. Centralized Logging

**File**: `app/utils/logger.py`

```python
def get_logger(name: str) -> logging.Logger:
    # Returns configured logger with JSON formatter
    # Outputs: timestamp, level, message, request_id, module, function
    # Never logs: passwords, tokens, sensitive data

# JSON output format:
# {
#   "timestamp": "2026-02-19T10:30:45.123Z",
#   "level": "INFO",
#   "message": "User registered successfully",
#   "request_id": "abc123-def456",
#   "user_id": 123,
#   "module": "auth_service"
# }
```

**What it does**:
- Provides structured JSON logging for all components
- Includes request ID for traceability
- Filters sensitive data automatically
- Supports different log levels for development/production

---

### 8. Circuit Breaker Pattern

**File**: `app/utils/circuit_breaker.py`

```python
class CircuitBreaker:
    # States: CLOSED (normal) -> OPEN (fail-fast) -> HALF_OPEN (recovery)

    def __call__(self, func):
        # Decorator pattern
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check state
            # Execute function
            # Track failures
            # Raise CircuitBreakerOpenException if open
        return wrapper

# Configurable:
# - failure_threshold: Open after N failures
# - recovery_timeout: Try recovery after N seconds
# - expected_exception: What counts as failure
```

**What it does**:
- Implements circuit breaker pattern for fault tolerance
- Prevents cascading failures
- Allows graceful recovery
- Can be applied to database operations, external API calls, etc.

---

### 9. Custom Exception Hierarchy

**File**: `app/exceptions.py`

```python
class AuthException(Exception):
    error_code: str
    status_code: int = 401

class InvalidCredentialsException(AuthException):
    error_code = "INVALID_CREDENTIALS"

class TokenExpiredException(AuthException):
    error_code = "TOKEN_EXPIRED"

class ValidationException(Exception):
    error_code: str
    status_code: int = 400

class DuplicateEmailException(ValidationException):
    error_code = "DUPLICATE_EMAIL"

class CircuitBreakerOpenException(Exception):
    error_code = "SERVICE_UNAVAILABLE"
    status_code: int = 503
```

**What it does**:
- Provides clear exception hierarchy
- Each exception has error_code and status_code
- Enables specific error handling in middleware

---

### 10. Request ID Middleware

**File**: `app/middleware/logging.py`

```python
async def request_id_middleware(request: Request, call_next):
    # Generate unique UUID for request
    request_id = str(uuid.uuid4())
    # Add to request state
    request.state.request_id = request_id
    # Add to context (for logging)
    # Log: method, path, status_code, response_time, request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

**What it does**:
- Assigns unique ID to every request
- Includes in all logs for traceability
- Returns in response headers for client correlation
- Enables debugging of specific requests

---

### 11. Exception Handler Middleware

**File**: `app/middleware/exception.py`

```python
async def exception_handler(request: Request, exc: Exception):
    # Catch all exceptions
    # Log exception details (with stack trace in dev)
    # Return JSON response with:
    # - detail: user-friendly message
    # - error_code: machine-readable code
    # - status_code: HTTP status
    # - timestamp: ISO format
    # - request_id: from request state

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail,
            "error_code": error_code,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.state.request_id
        }
    )
```

**What it does**:
- Catches all unhandled exceptions
- Returns consistent error response format
- Protects sensitive information (no stack traces to client)
- Logs full details server-side for debugging

---

### 12. Dependency Injection

**File**: `app/dependencies.py`

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Provides database session to routes
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    token: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Extract token from "Bearer {token}" format
    # Decode and validate token
    # Lookup user in database
    # Return User object or raise TokenInvalidException

def get_logger() -> logging.Logger:
    # Returns logger with current request context
```

**What it does**:
- Provides clean dependency injection
- Automatically validates authorization
- Injects User object into protected routes
- Enables easy testing via mock dependencies

---

### 13. User Service

**File**: `app/services/user_service.py`

```python
class UserService:
    async def create_user(self, db: AsyncSession, email: str, username: str, hashed_password: str) -> User:
        # Check for duplicates
        # Create and commit User
        # Raise DuplicateEmailException / DuplicateUsernameException

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        # Query by email (case-insensitive)
        # Return User or None

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        # Query by ID

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        # Query by username (case-insensitive)

    async def update_last_login(self, db: AsyncSession, user_id: int) -> None:
        # Update last_login timestamp
```

**What it does**:
- Encapsulates user data access logic
- Provides single source of truth for user operations
- Reusable across different interfaces (API, CLI, webhooks)
- Raises specific exceptions for error cases

---

### 14. Authentication Service

**File**: `app/services/auth_service.py`

```python
class AuthService:
    async def register_user(self, db: AsyncSession, email: str, username: str, password: str) -> TokenResponse:
        # Validate input (email format, password strength, username format)
        # Raise ValidationException for invalid inputs
        # Hash password
        # Create user via UserService
        # Generate access and refresh tokens
        # Return TokenResponse with tokens and user info

    async def login_user(self, db: AsyncSession, email: str, password: str) -> TokenResponse:
        # Lookup user by email
        # Raise InvalidCredentialsException if not found
        # Verify password
        # Raise InvalidCredentialsException if wrong
        # Update last_login timestamp
        # Generate tokens
        # Return TokenResponse

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        # Decode refresh token
        # Raise TokenExpiredException if expired
        # Raise TokenInvalidException if invalid
        # Generate new access token
        # Return TokenResponse with new access token

    async def validate_password_strength(self, password: str) -> bool:
        # Check minimum length (12 chars)
        # Check for complexity (uppercase, lowercase, digit, special)
        # Raise WeakPasswordException if invalid
```

**What it does**:
- Implements complete authentication workflows
- Validates all inputs
- Handles edge cases (duplicate users, weak passwords, etc.)
- Generates tokens with proper claims
- Logs authentication events (without sensitive data)

---

### 15. API Routes

**File**: `app/routes/auth.py`

```python
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", status_code=201, response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
) -> TokenResponse:
    # Validate input via Pydantic (automatic)
    # Call auth_service.register_user()
    # Return TokenResponse with 201 Created
    # Log registration attempt (without password)

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
    logger: logging.Logger = Depends(get_logger)
) -> TokenResponse:
    # Validate input
    # Call auth_service.login_user()
    # Return TokenResponse with 200 OK
    # Log login attempt

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    # Call auth_service.refresh_access_token()
    # Return new TokenResponse
```

**Documentation**: Each endpoint includes:
- Clear description
- Request/response examples
- Security annotations (JWT required for refresh)
- Possible error responses with examples

---

### 16. Health Check Route

**File**: `app/routes/health.py`

```python
router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> dict:
    # Return status and timestamp
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

**What it does**:
- Provides endpoint for load balancers
- Indicates service availability
- Can be extended with detailed health metrics

---

### 17. FastAPI Application

**File**: `app/main.py`

```python
app = FastAPI(
    title="Auth Service",
    description="Production-ready authentication API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Middleware order (important):
# 1. RequestIDMiddleware - Add unique request ID
# 2. LoggingMiddleware - Log all requests
# 3. ExceptionHandlerMiddleware - Catch exceptions
# 4. CORSMiddleware - Handle cross-origin requests (if needed)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)

# Swagger automatically generates from route docstrings and Pydantic models
```

**What it does**:
- Initializes FastAPI application
- Registers middleware in correct order
- Includes all routers
- Enables Swagger/OpenAPI documentation at /docs

---

### 18. Database Schema

**File**: `alembic/versions/001_create_users_table.py`

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

**What it does**:
- Creates users table with all required columns
- Defines UNIQUE constraints on email/username
- Creates indexes for fast lookups
- Provides audit timestamps

---

### 19. Testing Configuration

**File**: `tests/conftest.py`

```python
# Pytest fixtures:
# - event_loop: Async event loop for async tests
# - test_db: Isolated test database (reset per test)
# - async_client: TestClient for making requests
# - test_user: Sample user created in test database
# - valid_access_token: JWT token for test user
# - expired_token: Expired JWT for testing expiration handling

@pytest.fixture
async def test_db():
    # Create tables in test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield AsyncSessionLocal()
    # Drop tables after test
```

**What it does**:
- Sets up pytest for async testing
- Provides isolated database per test
- Creates test users and tokens
- Enables fast, reliable test execution

---

### 20. Unit Tests

**Files**:
- `tests/unit/test_auth_service.py`
- `tests/unit/test_user_service.py`
- `tests/unit/test_jwt_utils.py`
- `tests/unit/test_password_utils.py`

**Coverage**:
- Valid registration and login flows
- Duplicate email/username handling
- Invalid credentials
- Weak password validation
- Token creation and validation
- Token expiration
- Password hashing consistency

**Approach**:
- Mock database calls
- Test error paths
- Verify exceptions raised
- Check return values

---

### 21. Integration Tests

**Files**:
- `tests/integration/test_auth_routes.py`
- `tests/integration/test_protected_routes.py`

**Coverage**:
- HTTP endpoint behavior
- Request/response validation
- Status codes
- Error responses
- Protected route access
- Token validation in headers

**Approach**:
- Use TestClient to make HTTP requests
- Use real test database
- Verify full request/response cycle

---

## Database Schema

### Users Table

```
users
├── id (PRIMARY KEY, INTEGER, auto-increment)
├── username (VARCHAR(50), UNIQUE, NOT NULL)
├── email (VARCHAR(100), UNIQUE, NOT NULL, INDEXED)
├── hashed_password (VARCHAR(255), NOT NULL)
├── is_active (BOOLEAN, DEFAULT true)
├── created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
├── updated_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
└── last_login (TIMESTAMP, NULLABLE)
```

### Optional Future Tables

**refresh_tokens**: For token revocation and tracking
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- token_hash (UNIQUE)
- expires_at
- is_revoked
- created_at

**audit_logs**: For compliance and debugging
- id (PRIMARY KEY)
- user_id (FOREIGN KEY, NULLABLE)
- action (e.g., "login", "register", "password_change")
- resource (e.g., "user", "auth")
- details (JSON)
- ip_address
- user_agent
- created_at

---

## API Contracts

### 1. User Registration

**Endpoint**: `POST /api/auth/register`

**Request**:
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Validation**:
- email: Valid email format, not already in use
- username: 3-50 alphanumeric/underscore characters, not reserved, not already in use
- password: Minimum 12 characters, at least one uppercase, one lowercase, one digit, one special character

**Response** (201 Created):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "john_doe",
    "is_active": true,
    "created_at": "2026-02-19T10:30:45.123Z",
    "last_login": null
  }
}
```

**Error Responses**:
```json
// 400 Bad Request - Invalid email format
{
  "detail": "Invalid email format",
  "error_code": "INVALID_EMAIL",
  "status_code": 400,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}

// 400 Bad Request - Duplicate email
{
  "detail": "Email already registered",
  "error_code": "DUPLICATE_EMAIL",
  "status_code": 400,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}

// 400 Bad Request - Weak password
{
  "detail": "Password does not meet complexity requirements",
  "error_code": "WEAK_PASSWORD",
  "status_code": 400,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}
```

---

### 2. User Login

**Endpoint**: `POST /api/auth/login`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Validation**:
- email: Required (or username as alternative)
- password: Required, not empty

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "john_doe",
    "is_active": true,
    "created_at": "2026-02-19T10:30:45.123Z",
    "last_login": "2026-02-19T10:30:45.123Z"
  }
}
```

**Error Responses**:
```json
// 401 Unauthorized - Invalid credentials
{
  "detail": "Invalid email or password",
  "error_code": "INVALID_CREDENTIALS",
  "status_code": 401,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}

// 404 Not Found - User doesn't exist
{
  "detail": "User not found",
  "error_code": "USER_NOT_FOUND",
  "status_code": 404,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}
```

---

### 3. Token Refresh

**Endpoint**: `POST /api/auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "john_doe",
    "is_active": true,
    "created_at": "2026-02-19T10:30:45.123Z",
    "last_login": "2026-02-19T10:30:45.123Z"
  }
}
```

**Error Responses**:
```json
// 401 Unauthorized - Token expired
{
  "detail": "Refresh token has expired",
  "error_code": "TOKEN_EXPIRED",
  "status_code": 401,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}

// 401 Unauthorized - Invalid token
{
  "detail": "Invalid refresh token",
  "error_code": "TOKEN_INVALID",
  "status_code": 401,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}
```

---

### 4. Protected Route Example

**Endpoint**: `GET /api/user/profile` (Protected)

**Request**:
```
GET /api/user/profile
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "is_active": true,
  "created_at": "2026-02-19T10:30:45.123Z",
  "last_login": "2026-02-19T10:30:45.123Z"
}
```

**Error Responses**:
```json
// 401 Unauthorized - Missing token
{
  "detail": "Missing authorization token",
  "error_code": "MISSING_TOKEN",
  "status_code": 401,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}

// 401 Unauthorized - Invalid token
{
  "detail": "Invalid or expired token",
  "error_code": "TOKEN_INVALID",
  "status_code": 401,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "abc123"
}
```

---

## Interfaces & Function Signatures

### JWT Utilities

```python
def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""

def create_refresh_token(
    data: dict[str, Any]
) -> str:
    """Create JWT refresh token"""

def decode_token(
    token: str
) -> dict[str, Any]:
    """Decode and validate JWT token"""
    # Raises: TokenInvalidException, TokenExpiredException
```

### Password Utilities

```python
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against hash"""
```

### User Service

```python
class UserService:
    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        username: str,
        hashed_password: str
    ) -> User:
        """Create new user"""
        # Raises: DuplicateEmailException, DuplicateUsernameException

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """Get user by email (case-insensitive)"""

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[User]:
        """Get user by ID"""

    async def get_user_by_username(
        self,
        db: AsyncSession,
        username: str
    ) -> Optional[User]:
        """Get user by username (case-insensitive)"""

    async def update_last_login(
        self,
        db: AsyncSession,
        user_id: int
    ) -> None:
        """Update user's last login timestamp"""
```

### Auth Service

```python
class AuthService:
    async def register_user(
        self,
        db: AsyncSession,
        email: str,
        username: str,
        password: str
    ) -> dict[str, Any]:
        """Register new user and return tokens"""
        # Raises: ValidationException, DuplicateEmailException, DuplicateUsernameException

    async def login_user(
        self,
        db: AsyncSession,
        email: str,
        password: str
    ) -> dict[str, Any]:
        """Authenticate user and return tokens"""
        # Raises: InvalidCredentialsException, UserNotFoundException

    async def refresh_access_token(
        self,
        refresh_token: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Generate new access token from refresh token"""
        # Raises: TokenExpiredException, TokenInvalidException

    async def validate_password_strength(
        self,
        password: str
    ) -> bool:
        """Validate password meets complexity requirements"""
        # Raises: WeakPasswordException
```

### Dependencies

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session to routes"""

async def get_current_user(
    token: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate JWT and return current user"""
    # Raises: TokenInvalidException, TokenExpiredException, UserNotFoundException

def get_logger() -> logging.Logger:
    """Get logger with request context"""
```

---

## Trade-offs

### 1. JWT vs Sessions

**Choice**: JWT (stateless tokens)

**Pros**:
- Stateless: No server-side session storage needed
- Scalable: Works across multiple servers without coordination
- Microservice-friendly: Token can be passed between services
- Standard: JWT is industry-standard for APIs

**Cons**:
- Can't revoke instantly (tokens valid until expiration)
- Larger payload if many claims included
- Client must store securely (vulnerable to XSS)

**Mitigation**: Short access token expiration (30 min), long refresh token expiration (7 days)

---

### 2. Single Table vs Separate User/Profile Tables

**Choice**: Single users table

**Pros**:
- Simple schema, fewer JOINs
- Faster queries for common operations
- Easy to understand and maintain

**Cons**:
- Can't add complex user attributes later without migration
- Mixes different types of data

**Mitigation**: Can easily migrate to separate tables if needed without API changes

---

### 3. Database: SQLite vs PostgreSQL

**Choice**: SQLite for development, PostgreSQL for production

**Pros**:
- SQLite: No setup needed, embedded, great for development
- PostgreSQL: ACID compliance, better concurrency, suitable for production

**Cons**:
- SQLite: Not suitable for production (limited concurrency)
- PostgreSQL: Requires separate server setup

---

### 4. Structured Logging: structlog vs Python Logging

**Choice**: Python `logging` with custom JSON formatter

**Pros**:
- Built-in, no extra dependencies
- Familiar to most Python developers
- Can easily upgrade to structlog later

**Cons**:
- Less feature-rich than structlog
- More boilerplate for JSON formatting

---

### 5. Circuit Breaker: Custom vs library (pybreaker, tenacity)

**Choice**: Custom decorator implementation

**Pros**:
- Full control and understanding
- No external dependencies (for now)
- Easy to extend for specific needs

**Cons**:
- More code to maintain
- Less battle-tested than libraries

**Mitigation**: Can replace with library later if needed

---

## Backward Compatibility

The API is new, so no backward compatibility concerns. However, design decisions enable future extensions:

1. **User attributes**: Can add profile table without changing API
2. **Tokens**: Can implement token blacklist by adding refresh_tokens table
3. **Audit logging**: Can add audit_logs table for compliance
4. **Multi-factor authentication**: Can be added as additional check without API changes
5. **OAuth2**: Can be added as additional login method

---

## Open Questions for Implementation Phase

1. **Email Verification**: Should users verify email before login? (Recommendation: No for MVP, add in Phase 2)

2. **Rate Limiting**: Should we implement rate limiting on auth endpoints? (Recommendation: Yes, use slowapi library for FastAPI)

3. **CORS Configuration**: What origins should be allowed? (Recommendation: Configurable via .env, restricted list for production)

4. **Refresh Token Rotation**: Should refresh tokens be single-use? (Recommendation: Yes for security, requires refresh_tokens table)

5. **Password Reset**: Is this required for MVP? (Recommendation: No, add in Phase 4)

6. **Social Login**: Should we support OAuth2/Google/GitHub login? (Recommendation: No for MVP, add in future phase)

7. **Database**: SQLite for MVP or PostgreSQL? (Recommendation: SQLite for development, can switch to PostgreSQL for production)

8. **Logging**: Central log aggregation tool? (Recommendation: No for MVP, JSON output ready for future aggregation)

---

## Summary

This design provides a **production-ready foundation** that is:

✅ **Secure**: Passwords hashed with bcrypt, JWT for authentication, no sensitive data in logs
✅ **Observable**: Structured JSON logging with request IDs for traceability
✅ **Resilient**: Circuit breaker pattern for fault tolerance
✅ **Scalable**: Stateless JWT, async throughout, connection pooling
✅ **Maintainable**: Clear separation of concerns, dependency injection for testability
✅ **Well-documented**: Swagger/OpenAPI auto-generated, comprehensive docstrings
✅ **Extensible**: Can easily add features (2FA, email verification, OAuth2, etc.)

The implementation will follow this design strictly, with no scope creep beyond what's documented.
