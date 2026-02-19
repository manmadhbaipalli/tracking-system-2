# FastAPI Auth System - Technical Requirements

## Executive Summary

This document specifies a production-ready authentication system built with FastAPI, featuring JWT-based authentication, centralized logging, global exception handling, circuit breaker resilience, and complete Swagger API documentation. The system is designed for scalability, security, and maintainability.

---

## 1. Functional Requirements

### 1.1 Authentication Endpoints

#### 1.1.1 User Registration
**Endpoint**: `POST /api/auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePassword123!@#"
}
```

**Request Validation**:
- `email`: Valid email format (RFC 5322), not already registered
- `username`: 3-50 characters, alphanumeric + underscore/hyphen, unique
- `password`: Minimum 12 characters, must include uppercase, lowercase, digit, special char

**Response (201 Created)**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "is_active": true,
  "created_at": "2026-02-19T10:30:45.123Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid email format, weak password, username too short
- `409 Conflict`: Email already registered, username already taken
- `500 Internal Server Error`: Database error

**Validation Rules**:
- Email normalization: convert to lowercase before storage
- Username blocklist: prevent reserved names (admin, root, api, etc.)
- Password requirements: enforce strength rules (12+ chars, mixed case, numbers, symbols)
- Unique constraint: database-level unique index on email and username

---

#### 1.1.2 User Login
**Endpoint**: `POST /api/auth/login`

**Request Body** (Option 1 - Email):
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!@#"
}
```

**Request Body** (Option 2 - Username):
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!@#"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "john_doe",
    "is_active": true,
    "created_at": "2026-02-19T10:30:45.123Z",
    "last_login": "2026-02-19T10:35:20.456Z"
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials (never reveal which field is wrong)
- `404 Not Found`: User not found (return as 401 to prevent enumeration)
- `429 Too Many Requests`: Rate limit exceeded (5 attempts per minute per IP)
- `500 Internal Server Error`: Database error

**Side Effects**:
- Update user's `last_login` timestamp to current UTC time
- Log successful login with timestamp and IP address

---

#### 1.1.3 Token Refresh
**Endpoint**: `POST /api/auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses**:
- `401 Unauthorized`: Refresh token invalid, expired, or revoked
- `400 Bad Request`: Malformed token
- `500 Internal Server Error`: Database error

**Validation**:
- Token must be valid JWT with `token_type: "refresh"`
- Token must not be expired
- Token must not be revoked (if revocation tracking enabled)
- User must exist and be active

---

#### 1.1.4 User Logout (Optional)
**Endpoint**: `POST /api/auth/logout`

**Request Header**:
```
Authorization: Bearer {access_token}
```

**Response (200 OK)**:
```json
{
  "message": "Successfully logged out"
}
```

**Implementation Note**:
- Can be client-side only (delete local token)
- Optional server-side implementation: add token to blacklist (requires storage)
- For MVP, recommend client-side only (stateless)

---

### 1.2 Protected Route Pattern

**Example Protected Endpoint**: `GET /api/user/profile`

**Request**:
```
GET /api/user/profile
Authorization: Bearer {access_token}
```

**Response (200 OK)**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "is_active": true,
  "created_at": "2026-02-19T10:30:45.123Z",
  "last_login": "2026-02-19T10:35:20.456Z"
}
```

**Access Control**:
- All protected routes require valid, non-expired access token
- Token passed in `Authorization` header as `Bearer {token}`
- User object injected via `get_current_user()` dependency
- No additional database calls needed if JWT contains required data

---

## 2. Non-Functional Requirements

### 2.1 Centralized Logging System

**Logging Scope**:
- All HTTP requests: method, path, status code, response time, request ID
- Authentication events: registration, login, logout, token refresh, failures
- Business logic: user creation, validation failures, duplicate attempts
- Errors: exceptions, stack traces (development only), error details
- Database operations: query timing, connection pool stats
- Circuit breaker state changes: open, half-open, closed transitions

**Log Format**: Structured JSON (one JSON object per line)

**Required Fields in Every Log**:
```json
{
  "timestamp": "2026-02-19T10:30:45.123456Z",
  "level": "INFO",
  "service": "auth-api",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "User login successful",
  "logger": "auth_service"
}
```

**Optional Context Fields**:
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "username": "john_doe",
  "event": "user.login",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "duration_ms": 245,
  "path": "/api/auth/login",
  "method": "POST",
  "status_code": 200,
  "error_code": "invalid_credentials",
  "stack_trace": "[production: redacted, development: full]"
}
```

**Redacted Fields** (Never Log):
- Passwords (any form)
- Access tokens
- Refresh tokens
- JWT payloads
- API keys/secrets
- Credit card numbers
- SSN or personal ID numbers

**Log Levels**:
- `DEBUG`: Detailed internal state (development only)
- `INFO`: Normal operations (user actions, startups)
- `WARNING`: Unexpected conditions that don't prevent operation
- `ERROR`: Error conditions that need attention
- `CRITICAL`: System-level failures that require immediate action

**Logging Configuration**:
- Development: Log level = DEBUG, console output, all events
- Testing: Log level = WARNING, capture to file, no network I/O
- Production: Log level = INFO, JSON to syslog/aggregator, no stack traces

**Example Log Entries**:

Registration Success:
```json
{"timestamp":"2026-02-19T10:30:45.123Z","level":"INFO","service":"auth-api","request_id":"abc123","message":"User registration completed","event":"user.register","user_id":1,"email":"user@example.com","username":"john_doe","duration_ms":156}
```

Login Failure:
```json
{"timestamp":"2026-02-19T10:31:12.456Z","level":"WARNING","service":"auth-api","request_id":"def456","message":"Failed login attempt","event":"user.login_failed","email":"attacker@example.com","reason":"user_not_found","ip_address":"203.0.113.45","attempt_count":3}
```

Database Error:
```json
{"timestamp":"2026-02-19T10:32:01.789Z","level":"ERROR","service":"auth-api","request_id":"ghi789","message":"Database connection failed","event":"db.error","error_code":"DB_CONN_FAILED","error_type":"SQLAlchemyError","duration_ms":5000}
```

---

### 2.2 Centralized Exception Handling

**Requirement**: All exceptions must be caught and returned in consistent format.

**Error Response Format**:
```json
{
  "detail": "User-friendly error message",
  "error_code": "ERROR_CODE_IN_CAPS",
  "status_code": 400,
  "timestamp": "2026-02-19T10:30:45.123Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "path": "/api/auth/login"
}
```

**Exception Classes & HTTP Mappings**:

| Exception | HTTP Status | Error Code | Detail Message |
|-----------|-------------|------------|-----------------|
| InvalidCredentialsException | 401 | INVALID_CREDENTIALS | Invalid email/username or password |
| TokenExpiredException | 401 | TOKEN_EXPIRED | Access token has expired, please refresh |
| TokenInvalidException | 401 | TOKEN_INVALID | Invalid or malformed access token |
| UserNotFoundException | 404 | USER_NOT_FOUND | User not found |
| DuplicateEmailException | 409 | DUPLICATE_EMAIL | Email already registered |
| DuplicateUsernameException | 409 | DUPLICATE_USERNAME | Username already taken |
| WeakPasswordException | 400 | WEAK_PASSWORD | Password does not meet strength requirements |
| InvalidEmailException | 400 | INVALID_EMAIL | Email format is invalid |
| ValidationException | 400 | VALIDATION_ERROR | Input validation failed |
| DatabaseException | 500 | DATABASE_ERROR | Database operation failed (log full error) |
| CircuitBreakerOpenException | 503 | SERVICE_UNAVAILABLE | Service temporarily unavailable |
| RateLimitException | 429 | RATE_LIMIT_EXCEEDED | Too many requests, try again later |
| UnauthorizedException | 401 | UNAUTHORIZED | Authentication required |
| ForbiddenException | 403 | FORBIDDEN | You do not have permission to access this resource |

**Error Handling Rules**:
- Never expose stack traces to clients (production)
- Never reveal whether email/username exists (use generic "invalid credentials")
- Include timestamp and request_id for debugging
- Log all errors with appropriate level (WARNING for 4xx, ERROR for 5xx)
- Client receives user-friendly message, backend logs full details

**Example Exception Handlers**:

```python
@app.exception_handler(InvalidCredentialsException)
async def handle_invalid_credentials(request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "detail": "Invalid email/username or password",
            "error_code": "INVALID_CREDENTIALS",
            "status_code": 401,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request.state.request_id,
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def handle_generic_exception(request, exc):
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.error("Unhandled exception", extra={
        "request_id": request_id,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "path": request.url.path,
        "method": request.method
    }, exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id
        }
    )
```

---

### 2.3 Circuit Breaker Implementation

**Requirement**: Implement circuit breaker pattern for resilience.

**Circuit Breaker States**:

1. **Closed State** (Normal Operation)
   - All calls pass through
   - Failure counter incremented on each failure
   - When failures exceed threshold → transition to Open

2. **Open State** (Fail-Fast)
   - All calls immediately rejected with `CircuitBreakerOpenException`
   - Prevents cascading failures
   - After timeout duration → transition to Half-Open

3. **Half-Open State** (Recovery Test)
   - Limited calls allowed (e.g., 1 per second)
   - Success → transition to Closed
   - Failure → transition back to Open with reset timeout

**Configuration Parameters**:

```python
CIRCUIT_BREAKER_CONFIG = {
    "database": {
        "failure_threshold": 5,      # Open after N failures
        "timeout_seconds": 60,       # Time in Open state
        "half_open_max_calls": 1,    # Test calls in Half-Open
        "recovery_timeout": 30       # Time between test calls
    }
}
```

**Usage Example**:

```python
@circuit_breaker(service="database", threshold=5, timeout=60)
async def get_user_by_email(email: str) -> User:
    # Database call
    return await db.query(User).filter(User.email == email).first()
```

**Monitoring**:
- Log state transitions: Open → Closed
- Track time spent in each state
- Alert on prolonged Open state (> 5 minutes)
- Metrics: failure rate, recovery success rate

---

### 2.4 Swagger/OpenAPI Documentation

**Requirement**: All endpoints auto-documented with Swagger.

**Generated Documentation**:
- Available at `/docs` (Swagger UI)
- Available at `/redoc` (ReDoc)
- Available at `/openapi.json` (OpenAPI spec)

**Endpoint Documentation**:

```python
@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    tags=["Authentication"],
    summary="Register a new user",
    description="Create a new user account with email, username, and password.",
    responses={
        201: {
            "description": "User successfully registered",
            "model": RegisterResponse,
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "john_doe",
                "access_token": "eyJ...",
                "refresh_token": "eyJ...",
                "token_type": "bearer"
            }
        },
        400: {
            "description": "Validation error",
            "model": ErrorResponse,
            "example": {
                "detail": "Email format is invalid",
                "error_code": "INVALID_EMAIL",
                "status_code": 400
            }
        },
        409: {
            "description": "Email or username already exists",
            "model": ErrorResponse
        }
    }
)
async def register(request: RegisterRequest) -> RegisterResponse:
    """Register a new user account."""
    pass
```

**Documentation Requirements**:
- Every endpoint has summary and description
- Request/response schemas documented
- All error codes documented with examples
- Security scheme documented (JWT)
- Example values for all fields
- Default values documented

**Security Scheme**:

```python
security_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT access token"
)

@router.get(
    "/profile",
    response_model=UserResponse,
    security=[Depends(HTTPBearer())],
    tags=["User"],
    summary="Get user profile",
    description="Retrieve the authenticated user's profile information."
)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile."""
    pass
```

**Swagger UI Enhancements**:
- Authorize button with token input
- Try-it-out functionality on all endpoints
- Clear success/error response examples
- Request/response model schemas

---

## 3. Technical Specifications

### 3.1 JWT Token Specifications

**Access Token**:
- Algorithm: HS256 (HMAC with SHA-256)
- Expiration: 30 minutes (configurable)
- Payload:
  ```json
  {
    "sub": "1",           // User ID as string
    "exp": 1677000645,    // Expiration timestamp
    "iat": 1677000045,    // Issued at timestamp
    "token_type": "access",
    "email": "user@example.com"
  }
  ```

**Refresh Token**:
- Algorithm: HS256
- Expiration: 7 days (configurable)
- Payload:
  ```json
  {
    "sub": "1",
    "exp": 1677604845,
    "iat": 1676999045,
    "token_type": "refresh"
  }
  ```

**Token Storage**:
- Access token: In-memory on client (or localStorage, not recommended)
- Refresh token: HttpOnly secure cookie (recommended) or localStorage
- Never store in plaintext
- HttpOnly flag prevents JavaScript access (XSS protection)
- Secure flag requires HTTPS (enforced in production)

**Token Validation**:
- Verify signature with JWT secret key
- Check expiration time
- Verify token_type matches expected type
- Verify user still exists and is active

---

### 3.2 Password Requirements

**Strength Requirements**:
- Minimum length: 12 characters
- Must contain uppercase letter (A-Z)
- Must contain lowercase letter (a-z)
- Must contain digit (0-9)
- Must contain special character (!@#$%^&*)
- Cannot contain username
- Cannot be common password (check against password list)

**Hashing**:
- Algorithm: bcrypt (via passlib)
- Cost factor: 12 (iterations)
- Salt: Automatically generated by bcrypt
- Never store plaintext passwords

---

### 3.3 Database Connection Management

**Connection Pooling**:
- Pool size: 20 connections (production)
- Max overflow: 10 additional connections
- Pool timeout: 30 seconds
- Pool recycle: 3600 seconds (1 hour)

**Async Driver Selection**:
- SQLite (development): `aiosqlite`
- PostgreSQL (production): `asyncpg`

**Session Management**:
- Use async context managers for sessions
- Automatic rollback on exception
- Connection closed after request completes

---

### 3.4 Rate Limiting

**Login Endpoint Rate Limiting**:
- 5 requests per minute per IP address
- 10 requests per hour per email address
- Returns `429 Too Many Requests` when exceeded

**Registration Endpoint Rate Limiting**:
- 3 requests per hour per IP address
- Returns `429 Too Many Requests` when exceeded

**Implementation**:
- Use Redis (for distributed systems)
- Use in-memory store (for single-server)
- IP address extracted from request headers
- X-Forwarded-For header considered for proxies

---

## 4. Security Requirements

### 4.1 Authentication Security
- [ ] Passwords hashed with bcrypt (never plaintext)
- [ ] JWT tokens signed with strong secret (min 32 chars)
- [ ] HTTPS enforced (production)
- [ ] No authentication info in logs
- [ ] No error messages revealing user existence

### 4.2 Data Security
- [ ] Sensitive fields never in error responses
- [ ] Database queries use parameterized statements (no SQL injection)
- [ ] CSRF tokens for state-changing operations (if applicable)
- [ ] Request body size limit enforced

### 4.3 API Security
- [ ] CORS configured to specific origins
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] Strict-Transport-Security (HSTS) in production
- [ ] Rate limiting on auth endpoints

### 4.4 Logging Security
- [ ] Passwords never logged
- [ ] Tokens never logged
- [ ] API keys never logged
- [ ] Personal identifiable information minimized
- [ ] Audit trail for sensitive operations

---

## 5. Testing Requirements

### 5.1 Unit Tests

**Coverage Target**: 85%+

**Test Files**:
- `tests/unit/test_password_util.py` - Password hashing/verification
- `tests/unit/test_jwt_util.py` - Token creation/validation
- `tests/unit/test_auth_service.py` - Registration, login logic
- `tests/unit/test_user_service.py` - User CRUD operations
- `tests/unit/test_exceptions.py` - Exception handling
- `tests/unit/test_circuit_breaker.py` - Circuit breaker logic

**Test Cases**:
- Password hashing deterministic (same input, different hash)
- Password verification correct/incorrect
- JWT token creation and decoding
- Token expiration handling
- User registration with valid/invalid inputs
- User login with correct/incorrect credentials
- Duplicate email/username detection
- Circuit breaker state transitions

---

### 5.2 Integration Tests

**Test Files**:
- `tests/integration/test_auth_routes.py` - API endpoints
- `tests/integration/test_database.py` - Database operations
- `tests/integration/test_middleware.py` - Middleware chain
- `tests/integration/test_error_handling.py` - Exception handling end-to-end

**Test Cases**:
- POST /api/auth/register full flow
- POST /api/auth/login full flow
- POST /api/auth/refresh full flow
- Protected route with valid token
- Protected route with invalid token
- Protected route with expired token
- Error response format validation
- Logging output validation
- Concurrent registration attempts

---

### 5.3 Test Fixtures

**conftest.py Fixtures**:
```python
@pytest.fixture
async def db_session():
    """Test database session."""

@pytest.fixture
def user_factory():
    """Create test users."""

@pytest.fixture
def valid_token_factory():
    """Create valid JWT tokens."""

@pytest.fixture
def expired_token_factory():
    """Create expired JWT tokens."""

@pytest.fixture
async def client():
    """Test client for API calls."""
```

---

## 6. Deployment & Configuration

### 6.1 Environment Variables

**Required**:
```
DATABASE_URL=postgresql://user:password@localhost/dbname
JWT_SECRET_KEY=your-secret-key-min-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=production
```

**Optional**:
```
LOG_LEVEL=INFO
DATABASE_MAX_POOL_SIZE=20
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
CORS_ORIGINS=["https://example.com"]
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW=60
```

### 6.2 Application Startup

**Health Check Endpoint**:
```
GET /health
Response: {"status": "ok", "version": "1.0.0"}
```

**Startup Sequence**:
1. Load configuration from environment
2. Initialize database connection
3. Run database migrations
4. Initialize logging system
5. Create FastAPI app with middleware
6. Register exception handlers
7. Start Uvicorn server

---

## 7. Performance Requirements

**Response Time SLAs**:
- Registration: < 500ms (p95)
- Login: < 300ms (p95)
- Token refresh: < 200ms (p95)
- Protected routes: < 100ms (p95)

**Throughput**:
- 1000+ concurrent users
- 100+ requests per second
- Database: support 5000+ users

**Database**:
- Query time: < 10ms for user lookups (with index)
- Connection pool: max 20 active connections
- Transaction isolation: Read Committed minimum

---

## 8. Monitoring & Observability

**Metrics to Track**:
- Request count and latency by endpoint
- Error rate by error_code
- User registration and login counts
- Token refresh rate
- Circuit breaker state transitions
- Database connection pool utilization
- Slowest queries

**Logging Aggregation**:
- Centralized log collection (ELK, Splunk, etc.)
- Query logs by request_id for debugging
- Alert on error rate > 1%
- Alert on circuit breaker Open state > 5 min

---

## 9. Compliance & Standards

**Standards Compliance**:
- RFC 5322: Email format validation
- RFC 7519: JWT specification
- OWASP Top 10: Security guidelines
- PCI DSS: If handling credit cards (N/A for auth only)

**Documentation Standards**:
- API documented via OpenAPI 3.0 spec
- Code comments for complex logic only
- Type hints on all functions
- Docstrings for modules and classes

---

## 10. Success Acceptance Criteria

✅ **All Requirements Met When**:
- [ ] All endpoints implemented and tested
- [ ] Centralized logging captures all events in JSON format
- [ ] Exception handler returns consistent error format for all cases
- [ ] Circuit breaker prevents cascading failures
- [ ] Swagger documentation complete and accessible
- [ ] Database schema created with proper constraints
- [ ] Unit tests: 85%+ coverage, all passing
- [ ] Integration tests: all passing
- [ ] No sensitive data in logs or error responses
- [ ] Rate limiting working on auth endpoints
- [ ] Password strength validation enforced
- [ ] JWT tokens validated on protected routes
- [ ] Performance benchmarks met (response time SLAs)
- [ ] Code follows project conventions (CLAUDE.md)
- [ ] All documentation complete and accurate

---

## Appendix A: API Endpoint Summary

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | /api/auth/register | No | Create new user account |
| POST | /api/auth/login | No | Authenticate and receive tokens |
| POST | /api/auth/refresh | No | Refresh access token |
| POST | /api/auth/logout | Yes | Logout user (optional) |
| GET | /api/user/profile | Yes | Get authenticated user profile |
| GET | /health | No | Health check endpoint |
| GET | /docs | No | Swagger API documentation |
| GET | /redoc | No | ReDoc API documentation |
| GET | /openapi.json | No | OpenAPI 3.0 specification |

---

## Appendix B: Database Schema DDL

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Refresh tokens table (optional)
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Audit logs table (optional)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

---

This comprehensive requirements document provides the foundation for the implementation phase. All subsequent agents should reference this document when building the FastAPI authentication system.
