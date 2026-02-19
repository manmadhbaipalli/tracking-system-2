# FastAPI Authentication Service - Technical Design

**Date**: 2026-02-19
**Phase**: Design
**Project**: Auth Service
**Status**: 🏗️ DESIGN COMPLETE - Ready for Implementation

---

## Table of Contents

1. [Approach](#1-approach)
2. [Detailed Changes](#2-detailed-changes)
3. [Interfaces](#3-interfaces)
4. [Architecture Diagrams](#4-architecture-diagrams)
5. [Trade-offs](#5-trade-offs)
6. [Open Questions](#6-open-questions)

---

## 1. Approach

### 1.1 High-Level Solution Strategy

The FastAPI Authentication Service will be built following a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│         FastAPI Application         │
│  (Main App + Route Handlers)        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│     Middleware Layer                │
│  - Logging (correlation IDs)        │
│  - Exception Handling               │
│  - Request/Response Tracking        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Router Layer (API Endpoints)      │
│  - /api/v1/auth/register            │
│  - /api/v1/auth/login               │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│     Service Layer                   │
│  - AuthService (business logic)     │
│  - CircuitBreaker (fault tolerance) │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│     Data Access Layer               │
│  - SQLAlchemy ORM                   │
│  - User Model                       │
│  - LoginAttempts Model              │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│     PostgreSQL Database             │
└─────────────────────────────────────┘
```

### 1.2 Core Components

#### **1. User Registration Flow**
- Accept: `username`, `email`, `password`
- Validate: format, uniqueness, password strength
- Hash: password with bcrypt (cost 12)
- Store: user record in database
- Response: JWT token + user data (201 Created)

#### **2. User Login Flow**
- Accept: `username` OR `email` + `password`
- Check: rate limiting (5 attempts / 15 minutes)
- Check: account lock status
- Verify: password against bcrypt hash
- Generate: JWT token (30-minute expiry)
- Response: token + user data (200 OK)
- Track: login attempts in database

#### **3. Centralized Logging System**
- Generate: correlation ID per request (UUID)
- Log: request arrival (method, path, IP)
- Log: response completion (status, duration)
- Log: all errors with stack trace
- Filter: sensitive data (passwords, tokens)
- Format: JSON structured logging

#### **4. Centralized Exception Handling**
- Custom exceptions for each error type
- Global exception handlers mapping to HTTP codes
- Consistent response format: `{error, message, detail, timestamp, path}`
- No sensitive data in error responses

#### **5. Circuit Breaker Pattern**
- States: CLOSED → OPEN → HALF_OPEN
- Monitor: external service calls
- Graceful degradation: fail fast when service down
- Configurable: threshold and timeout

#### **6. Swagger/OpenAPI Documentation**
- Auto-generated from Pydantic schemas
- Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- All endpoints documented with examples
- Error responses documented

---

## 2. Detailed Changes

### 2.1 Directory Structure & New Files

The implementation will create/modify these files:

#### **Core Application Files**

```
app/
├── __init__.py                          # Empty init
├── main.py                              # FastAPI app initialization & middleware
├── config.py                            # Configuration & environment variables
│
├── models/
│   ├── __init__.py
│   └── user.py                          # SQLAlchemy User & LoginAttempts models
│
├── schemas/
│   ├── __init__.py
│   └── user.py                          # Pydantic schemas (RegisterRequest, LoginRequest, etc.)
│
├── database/
│   ├── __init__.py
│   └── connection.py                    # Database engine, session factory, base class
│
├── handlers/
│   ├── __init__.py
│   └── exceptions.py                    # Custom exceptions & exception handlers
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py                  # Authentication business logic
│   └── circuit_breaker.py               # Circuit breaker implementation
│
├── routers/
│   ├── __init__.py
│   └── auth.py                          # /register & /login endpoints
│
├── middleware/
│   ├── __init__.py
│   └── logging.py                       # Logging middleware with correlation IDs
│
└── utils/
    ├── __init__.py
    └── security.py                      # Password hashing, JWT utilities
```

#### **Configuration & Setup Files**

```
root/
├── CLAUDE.md                            # Existing - project standards
├── README.md                            # Project documentation
├── requirements.txt                     # Python dependencies
├── .env.example                         # Example environment variables
├── .gitignore                           # Git ignore rules
├── pytest.ini                           # Pytest configuration
├── pyproject.toml                       # Build configuration (optional)
│
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                        # Generated migration files
│
└── tests/                               # Test suite (design phase scope)
    ├── __init__.py
    ├── conftest.py                      # Pytest fixtures & configuration
    ├── test_auth_endpoints.py            # Integration tests
    ├── test_auth_service.py              # Unit tests
    ├── test_circuit_breaker.py           # Circuit breaker tests
    ├── test_exceptions.py                # Exception handling tests
    ├── test_logging.py                   # Logging middleware tests
    ├── test_security.py                  # Security utility tests
    └── test_models.py                    # ORM model tests
```

#### **Artifact/Design Files**

```
artifacts/test-design/
├── design.md                            # This file
├── features.json                        # Implementation contract (next section)
├── diagrams/
│   ├── sequence-register.puml           # PlantUML sequence diagram
│   ├── sequence-login.puml              # PlantUML sequence diagram
│   ├── flow-circuit-breaker.puml        # PlantUML flow diagram
│   └── architecture.puml                # System architecture diagram
└── database-schema.sql                  # SQL schema definition
```

### 2.2 Database Schema

#### **users table**

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### **login_attempts table**

```sql
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    ip_address VARCHAR(45)
);

CREATE INDEX idx_login_attempts_user_id ON login_attempts(user_id);
CREATE INDEX idx_login_attempts_timestamp ON login_attempts(attempted_at);
```

### 2.3 Configuration Management

#### **config.py**

Key configuration variables:

```python
# Database
DATABASE_URL: str  # PostgreSQL async URL
SQLALCHEMY_ECHO: bool = False

# JWT
SECRET_KEY: str  # Random secret for signing
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

# Security
MAX_LOGIN_ATTEMPTS: int = 5
LOGIN_ATTEMPT_TIMEOUT: int = 900  # 15 minutes in seconds

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # seconds

# Logging
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "json"  # or "plaintext"

# Password Validation
MIN_PASSWORD_LENGTH: int = 8
REQUIRE_PASSWORD_UPPERCASE: bool = True
REQUIRE_PASSWORD_LOWERCASE: bool = True
REQUIRE_PASSWORD_DIGIT: bool = True
REQUIRE_PASSWORD_SPECIAL: bool = True

# Rate Limiting
RATE_LIMIT_ENABLED: bool = True
```

---

## 3. Interfaces

### 3.1 API Endpoints

#### **POST /api/v1/auth/register**

**Request Body (Pydantic):**
```python
class RegisterRequest(BaseModel):
    username: str  # 3-32 chars, alphanumeric + underscore
    email: EmailStr
    password: str  # 8+ chars, upper, lower, digit, special
```

**Response (201 Created):**
```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    token: str  # JWT access token
    token_type: str = "bearer"
```

**Error Responses:**
- 422: Validation errors (invalid format, too short, etc.)
- 409: Duplicate user (username or email exists)
- 500: Database error

#### **POST /api/v1/auth/login**

**Request Body (Pydantic):**
```python
class LoginRequest(BaseModel):
    username: Optional[str] = None  # Required if email not provided
    email: Optional[EmailStr] = None  # Required if username not provided
    password: str

    @validator('root')
    def username_or_email(cls, v):
        if not v.get('username') and not v.get('email'):
            raise ValueError('Either username or email required')
        return v
```

**Response (200 OK):**
```python
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str
    expires_in: int  # seconds
```

**Error Responses:**
- 401: Invalid credentials or user not found
- 423: Account locked (too many failed attempts)
- 429: Rate limit exceeded
- 500: Database error

#### **GET /docs** (Swagger UI)
- Auto-generated by FastAPI
- Shows all endpoints with request/response examples

#### **GET /openapi.json**
- OpenAPI 3.0.0 specification
- Used by documentation tools

### 3.2 Service Layer Interfaces

#### **AuthService**

```python
class AuthService:
    async def register_user(
        self,
        username: str,
        email: str,
        password: str
    ) -> User:
        """Register a new user."""

    async def authenticate_user(
        self,
        username_or_email: str,
        password: str,
        ip_address: str
    ) -> User:
        """Authenticate a user by credentials."""

    async def validate_username(self, username: str) -> None:
        """Validate username format and uniqueness."""

    async def validate_email(self, email: str) -> None:
        """Validate email format and uniqueness."""

    async def validate_password(self, password: str) -> None:
        """Validate password strength requirements."""

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username."""

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email."""
```

#### **CircuitBreaker**

```python
class CircuitBreaker:
    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection."""

    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state."""

    @property
    def state(self) -> CircuitState:
        """Get current state: CLOSED, OPEN, or HALF_OPEN."""
```

### 3.3 Exception Hierarchy

```python
class AppException(Exception):
    """Base exception for all application errors."""
    status_code: int
    error_code: str
    detail: str

class ValidationError(AppException):
    status_code = 422
    error_code = "VALIDATION_ERROR"

class DuplicateUserError(AppException):
    status_code = 409
    error_code = "DUPLICATE_USER"

class AuthenticationError(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"

class AccountLockedError(AppException):
    status_code = 423
    error_code = "ACCOUNT_LOCKED"

class RateLimitError(AppException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"

class DatabaseError(AppException):
    status_code = 500
    error_code = "DATABASE_ERROR"

class CircuitBreakerError(AppException):
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"
```

### 3.4 Middleware Interfaces

#### **LoggingMiddleware**

- Intercepts all requests/responses
- Generates correlation ID
- Logs request: method, path, headers, IP
- Logs response: status, duration
- Filters sensitive data (passwords, tokens)
- Adds correlation ID to response headers

---

## 4. Architecture Diagrams

### 4.1 Registration Sequence Diagram

```plaintext
User → FastAPI → LoggingMiddleware → AuthRouter → AuthService → Database
  │       │          │                  │            │            │
  │       │          │ generate corr_id │            │            │
  │       │          │←────────────────│            │            │
  │       │          │                  │            │            │
  │───register───────→ log_request()  ──→ validate   │            │
  │       │          │                  │  schema    │            │
  │       │          │                  │            │            │
  │       │          │                  ├──validate──→ check_unique│
  │       │          │                  │ username   │            │
  │       │          │                  │            │            │
  │       │          │                  ├──validate──→ check_unique│
  │       │          │                  │ email      │            │
  │       │          │                  │            │            │
  │       │          │                  ├──validate──→ password
  │       │          │                  │ password   │ strength
  │       │          │                  │            │
  │       │          │                  ├──hash_pw──→
  │       │          │                  │            │
  │       │          │                  ├──create───→ INSERT user
  │       │          │                  │ user       │
  │       │          │                  │            │ 201 Created
  │       │          │                  ←─token──────│
  │       │          │ log_response()←──│            │
  │       │          │                  │            │
  │←────token────────│                  │            │
```

### 4.2 Login with Rate Limiting Sequence

```plaintext
User → FastAPI → LoggingMiddleware → AuthRouter → AuthService → Database
  │       │          │                  │            │            │
  │       │          │                  │            │            │
  │───login──────────→ log_request()  ──→ validate   │            │
  │       │          │                  │  schema    │            │
  │       │          │                  │            │            │
  │       │          │                  ├──check────→ rate_limit  │
  │       │          │                  │ rate_limit │ check      │
  │       │          │                  │            │            │
  │       │          │              [LIMIT EXCEEDED]│            │
  │       │          │ log error ←──raise RateLimit │            │
  │       │          │                  │            │            │
  │       │          │              [PASSED]         │            │
  │       │          │                  │            │            │
  │       │          │                  ├──find────→ SELECT user  │
  │       │          │                  │ user       │            │
  │       │          │                  │            │            │
  │       │          │              [NOT FOUND]      │            │
  │       │          │ log error ←──raise Auth      │            │
  │       │          │                  │            │            │
  │       │          │              [FOUND]          │            │
  │       │          │                  │            │            │
  │       │          │                  ├──verify───→ bcrypt      │
  │       │          │                  │ password   │ check      │
  │       │          │                  │            │            │
  │       │          │              [MISMATCH]       │            │
  │       │          │                  │            │            │
  │       │          │                  ├──record───→ INSERT fail │
  │       │          │                  │ attempt    │ attempt    │
  │       │          │ log error ←──raise Auth      │            │
  │       │          │                  │            │            │
  │       │          │              [MATCH]          │            │
  │       │          │                  │            │            │
  │       │          │                  ├──generate→ JWT token    │
  │       │          │                  │ token      │            │
  │       │          │                  │            │            │
  │       │          │                  ├──update───→ UPDATE last  │
  │       │          │                  │ last_login │ login_at   │
  │       │          │                  │            │            │
  │       │          │                  ├──record───→ INSERT succ  │
  │       │          │                  │ attempt    │ attempt    │
  │       │          │                  │            │            │
  │       │          │ log_response()←──token──────│            │
  │       │          │                  │            │            │
  │←────token────────│                  │            │            │
```

### 4.3 Circuit Breaker State Machine

```plaintext
┌─────────────────────────────────────────────────────────┐
│                 CIRCUIT BREAKER STATES                  │
└─────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │    CLOSED    │
                    │ (operational)│
                    └──────┬───────┘
                           │
                  ┌────────┴────────┐
                  │                 │
            Success            Failure
                  │                 │
                  │            Failure Count >= Threshold
                  │                 │
                  │        ┌────────▼─────────┐
                  │        │      OPEN        │
                  │        │  (circuit open)  │
                  │        └────────┬─────────┘
                  │                 │
                  │        Timeout Elapsed
                  │                 │
                  │        ┌────────▼──────────┐
                  │        │   HALF_OPEN       │
                  │        │  (testing)        │
                  │        └────────┬──────────┘
                  │                 │
                  │        ┌────────┴────────┐
                  │        │                 │
                  │    Success          Failure
                  │        │                 │
                  │        │    Reset to OPEN
                  │        │    Restart Timer
                  │        │                 │
                  └────────►CLOSED           │
                           │◄────────────────┘
```

---

## 5. Trade-offs

### 5.1 Database Choice: PostgreSQL

**Why PostgreSQL?**
- ✅ Robust, production-ready ACID compliance
- ✅ Excellent async support via asyncpg
- ✅ Strong SQL standard compliance
- ✅ Mature with excellent tooling

**Considered Alternatives:**
- MongoDB: No ACID guarantees needed for auth (rejected)
- SQLite: Single-threaded, not suitable for production (rejected)
- MySQL: Similar to PostgreSQL but RDBMS choice from spec

### 5.2 ORM: SQLAlchemy 2.0 (Async)

**Why SQLAlchemy?**
- ✅ Async support out of the box
- ✅ Type hints support
- ✅ Migration support via Alembic
- ✅ Flexible query building

**Considered Alternatives:**
- Raw SQL: More control, less abstraction (complexity)
- Django ORM: Requires full Django framework
- Tortoise ORM: Less mature than SQLAlchemy

### 5.3 JWT for Stateless Authentication

**Why JWT?**
- ✅ Stateless - no session storage needed
- ✅ Scalable across multiple servers
- ✅ Self-contained with user info
- ✅ Client-side verification possible

**Trade-off:**
- ❌ Token revocation requires blacklist (out of scope)
- ❌ Token size larger than session ID

### 5.4 Circuit Breaker Pattern

**Why Circuit Breaker?**
- ✅ Prevents cascading failures
- ✅ Fast fail when external service down
- ✅ Automatic recovery testing

**Implementation Approach:**
- Simple in-memory implementation (not distributed)
- Suitable for single-instance deployment
- Can be extended to distributed later

**Alternative:**
- Retry logic: Would mask failures longer
- Timeout-only: Would still timeout on failures

### 5.5 Synchronous vs. Asynchronous

**Why Async?**
- ✅ FastAPI is async-first
- ✅ Better resource utilization (I/O bound operations)
- ✅ Can handle more concurrent requests

**Trade-off:**
- ❌ More complex testing (pytest-asyncio)
- ❌ Entire stack must be async

### 5.6 Password Hashing: Bcrypt with Cost 12

**Why Bcrypt?**
- ✅ Industry standard
- ✅ Slow by design (resistant to brute force)
- ✅ Built into passlib

**Why Cost 12?**
- ✅ Good balance: ~250ms hashing time
- ✅ Resistant to modern GPU attacks
- ✅ Can be increased later if needed

### 5.7 Logging: JSON Structured Logs

**Why JSON?**
- ✅ Machine-parseable for log aggregation
- ✅ Structured context (correlation IDs, user_id)
- ✅ Easy filtering and analysis

**Alternative (plaintext):**
- More human-readable
- Harder to parse at scale

### 5.8 Centralized vs. Distributed Exception Handling

**Why Centralized?**
- ✅ Consistent error format across all endpoints
- ✅ Easier to change error format globally
- ✅ Single source of truth for error codes

**Implementation:**
- Global exception handlers via `@app.exception_handler`
- Custom exception classes with metadata

---

## 6. Open Questions

### 6.1 Implementation Decisions

1. **Token Refresh Mechanism**
   - Should we implement refresh tokens for extended sessions?
   - **Assumption**: No - 30-min access tokens only (out of scope)

2. **Email Verification**
   - Should registration require email verification?
   - **Assumption**: No - user can register and login immediately

3. **Password Reset**
   - Should we implement password reset endpoints?
   - **Assumption**: No - out of scope for this phase

4. **User Deactivation**
   - Should we support user account deactivation?
   - **Assumption**: No - accounts persist indefinitely

5. **API Versioning**
   - How deep should versioning be? (Currently `/api/v1/`)
   - **Assumption**: Single version endpoint, upgrade in place

### 6.2 Database & Storage

6. **Login Attempt History Retention**
   - How long should login attempts be kept?
   - **Assumption**: Keep indefinitely for audit trail

7. **User Soft Delete**
   - Should deleted users remain in database (soft delete)?
   - **Assumption**: Hard delete for this phase

### 6.3 Security & Compliance

8. **Password History**
   - Should we prevent reuse of recent passwords?
   - **Assumption**: No - out of scope

9. **Two-Factor Authentication**
   - Should we support 2FA?
   - **Assumption**: No - out of scope for this phase

10. **GDPR/Data Retention**
    - Should we implement data retention policies?
    - **Assumption**: Out of scope - rely on ops team

### 6.4 Performance & Scalability

11. **Rate Limiting Storage**
    - Should rate limit counters be in database or cache?
    - **Assumption**: Database for simplicity (Redis later if needed)

12. **Database Connection Pooling**
    - What's the optimal pool size?
    - **Assumption**: SQLAlchemy defaults (5-10 connections)

### 6.5 Testing & Deployment

13. **Database Migrations in Tests**
    - Should tests auto-migrate or use fixed schema?
    - **Assumption**: Auto-migrate from Alembic for each test session

14. **Deployment Environment**
    - Kubernetes, Docker, VM, or serverless?
    - **Assumption**: Docker Compose for development (ops team handles prod)

---

## 7. Implementation Checklist

### Phase 1: Infrastructure (Days 1-1)
- [ ] Create project structure
- [ ] Setup requirements.txt with dependencies
- [ ] Create .env.example and .gitignore
- [ ] Configure pytest and pytest.ini
- [ ] Create conftest.py with fixtures

### Phase 2: Core Models & Database (Days 1-2)
- [ ] Create User SQLAlchemy model
- [ ] Create LoginAttempts model
- [ ] Create Alembic migration
- [ ] Setup database connection
- [ ] Create Pydantic schemas

### Phase 3: Authentication Service (Days 2-3)
- [ ] Implement security utilities (hashing, JWT)
- [ ] Implement AuthService class
- [ ] Implement password validation
- [ ] Implement rate limiting logic
- [ ] Implement account locking logic

### Phase 4: API Endpoints (Days 3-4)
- [ ] Create auth router
- [ ] Implement /register endpoint
- [ ] Implement /login endpoint
- [ ] Add request/response validation

### Phase 5: Exception Handling (Day 4)
- [ ] Define custom exceptions
- [ ] Create global exception handlers
- [ ] Implement consistent error format

### Phase 6: Logging & Middleware (Day 4-5)
- [ ] Implement logging middleware
- [ ] Add correlation ID generation
- [ ] Add request/response logging
- [ ] Filter sensitive data

### Phase 7: Circuit Breaker (Day 5)
- [ ] Implement CircuitBreaker class
- [ ] Add state machine logic
- [ ] Integrate with external service calls

### Phase 8: Swagger Documentation (Day 5)
- [ ] FastAPI auto-generates from schemas
- [ ] Add description decorators
- [ ] Verify /docs and /redoc

### Phase 9: Tests (Days 6-8)
- [ ] Unit tests for services
- [ ] Integration tests for endpoints
- [ ] End-to-end workflow tests
- [ ] Achieve 80%+ coverage

### Phase 10: Review & Optimization (Days 8-9)
- [ ] Code review against CLAUDE.md
- [ ] Performance review
- [ ] Security review
- [ ] Documentation

---

## Summary

This technical design provides:

✅ **Clear Architecture** - Layered design with separation of concerns
✅ **API Contracts** - Well-defined request/response schemas
✅ **Database Schema** - Normalized design with proper indexes
✅ **Exception Strategy** - Consistent error handling across app
✅ **Logging Design** - Structured JSON with correlation tracking
✅ **Circuit Breaker** - Fault tolerance pattern for external calls
✅ **Trade-off Analysis** - Rationale for major decisions
✅ **Open Questions** - Documented assumptions for implementation

The design is ready for implementation in the next phase. All files to be created/modified are documented in features.json.

---

**Design Complete**: 2026-02-19
**Document Version**: 1.0
**Status**: 🟢 READY FOR IMPLEMENTATION
**Confidence Level**: HIGH
