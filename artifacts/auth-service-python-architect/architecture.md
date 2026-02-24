# Architecture: Auth Service (Python)

## Architecture Overview

**Style:** Layered Monolith
**Rationale:** The layered monolith is ideal for this MVP authentication service because:
- Clear separation of concerns (controller → service → repository)
- Simplicity and ease of development for a single-responsibility domain
- Straightforward testing at each layer
- Easy horizontal scaling (stateless design)
- Can be decomposed into microservices later if needed
- Well-suited for team collaboration with clear layer boundaries

### Component Diagram (Text)

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (Routers)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ AuthRouter   │  │ UserRouter   │  │ HealthRouter│  │
│  │(register,    │  │(me, update,  │  │(live, ready)│  │
│  │ login)       │  │ deactivate)  │  │             │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬───────┘  │
├─────────┼──────────────────┼─────────────────┼─────────┤
│ Middleware Layer                               │         │
│  ├─ CORSMiddleware                            │         │
│  ├─ CorrelationID middleware                  │         │
│  ├─ RequestLoggingMiddleware                  │         │
│  └─ ExceptionHandler (global)                 │         │
├─────────┼──────────────────┼─────────────────┼─────────┤
│         │          Service Layer              │         │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴──────┐ │
│  │ AuthService  │  │ UserService  │  │HealthService│ │
│  │(hashing,     │  │(profile ops, │  │(status)     │ │
│  │ JWT gen,     │  │ deactivate)  │  │             │ │
│  │ validation)  │  │              │  │             │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
├─────────┼──────────────────┼─────────────────┼─────────┤
│         │    Repository Layer (Data Access)  │         │
│  ┌──────┴───────┐  ┌──────┴───────────────────────┐  │
│  │ UserRepository │  (CRUD operations)               │  │
│  │(find_by_email,│                                  │  │
│  │ create, etc)  │                                  │  │
│  └──────┬───────┘  └──────────────┬─────────────────┘  │
├─────────┼──────────────────────────┼─────────────────┤
│ Security & Cross-Cutting            │                 │
│  ├─ security.py (JWT, BCrypt)      │                 │
│  ├─ exceptions.py (error handling)  │                 │
│  ├─ utils/circuit_breaker.py        │                 │
│  └─ utils/logging.py                │                 │
├─────────┴──────────────────────────┴─────────────────┤
│                   Data Layer                           │
│  ┌─────────────────────────────────────────────────┐  │
│  │        SQLAlchemy Models (Entities)              │  │
│  │  ├─ BaseModel (id, created_at, updated_at)      │  │
│  │  └─ User (email, password_hash, role, active)   │  │
│  └──────────────────────┬──────────────────────────┘  │
├────────────────────────┴────────────────────────────┤
│              Database (PostgreSQL/SQLite)            │
└─────────────────────────────────────────────────────┘
```

---

## Technology Decisions

| Category | Decision | Rationale |
|----------|----------|-----------|
| Language | Python 3.12 | Modern, async-ready, excellent for web services, broad ecosystem |
| Framework | FastAPI 0.100+ | Type-hinted, async-first, automatic OpenAPI/Swagger docs, high performance, built-in Pydantic validation |
| Database | PostgreSQL 16 (prod), SQLite (dev) | Relational, ACID, JSON support, easy migration via Alembic; SQLite for dev simplicity |
| ORM | SQLAlchemy 2.0+ | Async support, mature, parameterized queries prevent SQL injection, works with both PostgreSQL and SQLite |
| Authentication | JWT (HS256) | Stateless, scalable, no server-side session storage, suitable for distributed systems |
| Password Hashing | BCrypt (cost 12) | Industry standard, slow by design to resist brute force, works well with constant-time comparison |
| API Docs | FastAPI auto-docs | Free Swagger UI at `/docs`, auto-generated from type hints, no manual maintenance |
| Migrations | Alembic | Standard Python migration tool, works with SQLAlchemy, version-controlled schema changes |
| Logging | structlog + JSON | Structured logging enables log aggregation/parsing, correlation IDs for distributed tracing |
| Validation | Pydantic v2 | Built into FastAPI, type-safe, automatic OpenAPI schema generation, field-level error messages |
| Circuit Breaker | Custom implementation | Full control, lightweight, suitable for future external service calls |
| Build/Package | pip + requirements.txt | Simple, standard, works everywhere |

---

## Component Design

### 1. Router Layer (FastAPI Routers)
**Purpose:** Handle HTTP requests, validate input, serialize responses
**Dependencies:** Services, security utilities, Pydantic schemas
**Public API:** REST endpoints under `/api/v1/`

**Routers:**
- **auth.py** — `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- **users.py** — `GET /users/me`, `PATCH /users/me`, `DELETE /users/me`
- **admin.py** — `GET /users` (list), `PATCH /users/{id}/role`, `DELETE /users/{id}`
- **health.py** — `GET /health/live`, `GET /health/ready`

### 2. Service Layer
**Purpose:** Implement business logic, transaction management, orchestration
**Dependencies:** Repositories, security utilities
**Public API:** Service methods (register, login, get_user, update_profile, etc.)

**Services:**
- **auth_service.py** — Register, login, token refresh, JWT validation, BCrypt hashing
- **user_service.py** — Get profile, update profile, deactivate account
- **admin_service.py** — List users, update roles, deactivate users (admin ops)
- **health_service.py** — Check database connectivity, system status

### 3. Repository Layer
**Purpose:** Data access abstraction, CRUD operations
**Dependencies:** SQLAlchemy ORM, models
**Public API:** Repository methods (find_by_email, create, update, get_by_id, list, etc.)

**Repositories:**
- **user_repository.py** — All user CRUD operations with soft delete support

### 4. Model Layer (SQLAlchemy)
**Purpose:** Define entity structure and database schema
**Dependencies:** SQLAlchemy, database config
**Public API:** Model classes

**Models:**
- **base.py** — `BaseModel` with `id`, `created_at`, `updated_at` (auto-managed)
- **user.py** — `User` entity with email, password_hash, name, role, active

### 5. Schema Layer (Pydantic)
**Purpose:** Request/response validation and serialization
**Dependencies:** Pydantic v2
**Public API:** Pydantic models (DTOs)

**Schemas:**
- **auth.py** — `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `TokenResponse`
- **user.py** — `UserResponse`, `UpdateProfileRequest`
- **admin.py** — `UserListResponse`, `UpdateRoleRequest`
- **common.py** — `ErrorResponse`, `HealthResponse`, `PaginationParams`

### 6. Security Layer
**Purpose:** JWT generation/validation, password hashing, auth dependencies
**Dependencies:** PyJWT, bcrypt, FastAPI security
**Public API:** Functions and FastAPI Depends objects

**security.py:**
- `hash_password(password)` — BCrypt hashing
- `verify_password(plain, hash)` — Constant-time comparison
- `create_access_token(user_id, role, expiration)` — JWT generation
- `decode_token(token)` — JWT validation and extraction
- `get_current_user()` — FastAPI dependency for auth
- `require_admin()` — FastAPI dependency for admin-only endpoints

### 7. Exception Layer
**Purpose:** Custom exceptions, global exception handler
**Dependencies:** FastAPI exception handlers
**Public API:** Exception classes, handler middleware

**exceptions.py:**
- `ValidationError` — 400 Bad Request
- `AuthenticationError` — 401 Unauthorized
- `AuthorizationError` — 403 Forbidden
- `NotFoundError` — 404 Not Found
- `ConflictError` — 409 Conflict
- `ServiceUnavailableError` — 503 Service Unavailable
- `ErrorResponse` — Standard error response DTO

### 8. Middleware & Cross-Cutting Concerns
**Purpose:** Request/response processing, logging, error handling
**Dependencies:** FastAPI, structlog
**Public API:** Middleware functions, ASGI wrappers

**middleware.py:**
- `CORSMiddleware` — CORS configuration
- `CorrelationIDMiddleware` — Generate and propagate correlation IDs
- `RequestLoggingMiddleware` — Log all requests/responses
- `ExceptionHandlerMiddleware` — Catch all unhandled exceptions

### 9. Configuration Management
**Purpose:** Environment-based configuration, app initialization
**Dependencies:** Pydantic Settings, environment variables
**Public API:** Settings object

**config.py:**
- Pydantic `Settings` class with all config parameters
- Environment variable loading and validation
- Startup validation (fail-fast for missing required config)

### 10. Database Configuration
**Purpose:** SQLAlchemy engine, session management, connection pooling
**Dependencies:** SQLAlchemy, config
**Public API:** Engine, SessionLocal, get_db dependency

**database.py:**
- Create engine with connection pooling
- AsyncSession configuration
- `get_db()` dependency for routers

### 11. Utilities
**Purpose:** Circuit breaker, logging configuration, helpers
**Dependencies:** Various
**Public API:** Utility classes/functions

**utils/circuit_breaker.py:**
- `CircuitBreaker` class with CLOSED → OPEN → HALF_OPEN transitions
- Configurable thresholds (default 5 failures to open, 30s timeout)
- State tracking and health check integration

**utils/logging.py:**
- Structured logging configuration
- JSON formatter for production, readable for dev
- Correlation ID context tracking

### 12. Application Entry Point
**Purpose:** FastAPI app factory, middleware registration, startup/shutdown hooks
**Dependencies:** FastAPI, all layers
**Public API:** ASGI app

**main.py:**
- FastAPI app factory
- Register routers
- Register middleware/exception handlers
- Startup validation
- Graceful shutdown

---

## Data Flow

### Registration Flow
```
POST /api/v1/auth/register
↓
[CorrelationID middleware] → Generate UUID v4
↓
[Request validation] → Pydantic schema validates JSON
↓
AuthRouter.register()
↓
AuthService.register()
  ├─ Validate email format and uniqueness
  ├─ Hash password with BCrypt
  └─ Create user via UserRepository
↓
JWT generation → Create access token with user_id and role
↓
[Response serialization] → TokenResponse DTO
↓
200 Created + {"access_token": "...", "user_id": ..., ...}
```

### Login Flow
```
POST /api/v1/auth/login
↓
[Correlation ID] → Extract or generate
↓
[Request validation] → Email, password format check
↓
AuthRouter.login()
↓
AuthService.login()
  ├─ Validate email format
  ├─ Find user by email (UserRepository)
  ├─ Verify password (constant-time comparison)
  └─ If inactive user → reject with generic message
↓
JWT generation → Create access token
↓
200 OK + {"access_token": "...", "user_id": ..., ...}
```

### Authenticated Request Flow
```
GET /api/v1/users/me
↓
[CorrelationID middleware]
↓
[Authorization header] → Extract Bearer token
↓
security.get_current_user() dependency
  ├─ Validate JWT signature
  ├─ Check expiration
  ├─ Extract user_id and role
  └─ Verify user still exists and active
↓
UserRouter.get_me(current_user)
↓
UserService.get_profile(user_id)
  ├─ Fetch user from UserRepository
  └─ Return UserResponse DTO
↓
200 OK + {"id": ..., "email": "...", "name": "...", ...}
```

### Error Flow
```
POST /api/v1/auth/register (with invalid email)
↓
[Request validation] → Pydantic raises ValidationError
↓
[Global exception handler] → Catches all exceptions
  ├─ Extracts correlation_id from context
  ├─ Maps exception to HTTP status (400 for ValidationError)
  ├─ Logs error with correlation_id and stack trace
  └─ Serializes to ErrorResponse DTO
↓
400 Bad Request + {"status": 400, "code": "VALIDATION_ERROR", "message": "...", "correlation_id": "...", "errors": [...]}
```

---

## Security Architecture

### Authentication

**Method:** JWT (JSON Web Tokens) with HS256 (HMAC-SHA256)

**Token Structure:**
```json
{
  "sub": "123",                    // user_id
  "email": "user@example.com",    // for convenience (not a security claim)
  "role": "USER",                  // for authorization
  "iat": 1708779296,              // issued at
  "exp": 1708780196               // expires at (default: 15 minutes)
}
```

**Token Lifecycle:**
1. Generated on successful registration or login
2. Client stores in memory or localStorage
3. Client includes in `Authorization: Bearer <token>` header on protected requests
4. Server validates signature, expiration, and active user status on each request
5. Token cannot be revoked (stateless), only becomes invalid on expiration

**JWT Secret Management:**
- **Stored in environment variable:** `JWT_SECRET_KEY` (no default, required in production)
- **Minimum length:** 32 characters for HS256 (recommended 64+)
- **Never hardcoded** in source code
- **Rotation strategy:** Document separately (future phase)

### Authorization

**Access Control Matrix:**

| Endpoint Pattern | Anonymous | USER | ADMIN | Notes |
|------------------|-----------|------|-------|-------|
| POST /auth/register | ✓ | — | — | Public |
| POST /auth/login | ✓ | — | — | Public |
| POST /auth/refresh | ✓ | — | — | Public (with token) |
| GET /health/live | ✓ | — | — | Public liveness probe |
| GET /health/ready | ✓ | — | — | Public readiness probe |
| GET /docs | ✓ | — | — | Public (dev only) |
| GET /openapi.json | ✓ | — | — | Public (dev only) |
| GET /users/me | — | ✓ | ✓ | Own profile |
| PATCH /users/me | — | ✓ | ✓ | Own profile |
| DELETE /users/me | — | ✓ | ✓ | Own profile (soft delete) |
| GET /admin/users | — | — | ✓ | Admin list all users |
| PATCH /admin/users/{id}/role | — | — | ✓ | Admin role change |
| DELETE /admin/users/{id} | — | — | ✓ | Admin deactivate user |

**Enforcement Mechanisms:**
- **Role decorators/dependencies:** FastAPI `Depends` functions validate role
- **Resource ownership:** Service layer checks that USER can only access own profile
- **Admin endpoints:** Require `role == "ADMIN"` in JWT token

### Password Security

**Hashing Algorithm:** BCrypt with cost factor 12
- **Why BCrypt:** Designed to be slow (expensive), resists brute force, includes salt
- **Cost factor 12:** ~250ms per hash on modern hardware (acceptable for registration/login)
- **Constant-time comparison:** `bcrypt.checkpw()` prevents timing attacks

**Password Requirements:**
- Minimum 8 characters (enforced by Pydantic schema)
- No maximum length (bcrypt handles up to 72 bytes)
- No complexity requirements (not recommended by NIST)

**Storage:**
- Never store plain text password
- Store only `password_hash` column (255 chars for BCrypt output)
- Hashing happens server-side before database insert

### Input Validation

**Framework:** Pydantic v2 (built into FastAPI)

**Validation Strategy:**
- **Email:** RFC 5322 format validation, normalized to lowercase, uniqueness check at DB level
- **Password:** Minimum length 8, no format restrictions
- **Name:** Non-empty, max 100 characters, whitespace trimmed
- **Enums:** Role values strictly enum (USER, ADMIN)
- **Type safety:** Pydantic enforces type conversion (string → int, etc.)

**Error Response:**
```json
{
  "status": 422,
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "correlation_id": "...",
  "errors": [
    {"field": "email", "message": "Invalid email format"},
    {"field": "password", "message": "Ensure this value has at least 8 characters."}
  ]
}
```

### SQL Injection Prevention

**Mechanism:** SQLAlchemy ORM parameterization
- All queries built via ORM methods: `session.query()`, `session.execute(stmt)`
- **Never use string concatenation or format strings** in SQL
- Parameterized queries automatically escape user input

**Example (Safe):**
```python
stmt = select(User).where(User.email == email)  # Parameterized
user = session.scalars(stmt).first()
```

**Counter-example (Unsafe - FORBIDDEN):**
```python
# NEVER DO THIS:
stmt = f"SELECT * FROM users WHERE email = '{email}'"  # String interpolation
```

### CSRF Protection

**Mechanism:** Stateless JWT eliminates CSRF risk
- Browser cannot automatically include JWT in requests (unlike session cookies)
- CSRF tokens not needed for JSON APIs
- Additional protection: SameSite cookies (if using cookies for token storage)

### CORS Configuration

**Production:** Whitelist specific origins (no wildcard)
```python
allow_origins = ["https://app.example.com", "https://admin.example.com"]
```

**Development:** Allow localhost
```python
allow_origins = ["http://localhost:3000", "http://localhost:8080"]
```

**Configuration:** Via environment variable `CORS_ORIGINS` (comma-separated)

### OWASP API Top 10 Mitigations

1. **Broken Object-Level Authorization (BOLA)**
   - Mitigation: Check resource ownership in service layer
   - Example: USER can only update own profile, ADMIN can update any

2. **Broken Authentication**
   - Mitigation: JWT validation, BCrypt hashing, secure token generation
   - No hardcoded credentials, secrets in environment

3. **Broken Object Property-Level Authorization**
   - Mitigation: DTOs filter sensitive fields (never return `password_hash`)
   - Response schemas explicitly define returned fields

4. **Unrestricted Resource Consumption**
   - Mitigation: Pagination limits (max 100 items per page)
   - Future: Rate limiting at gateway level

5. **Broken Function-Level Authorization**
   - Mitigation: Role-based endpoint access via decorators
   - Admin endpoints reject USER role with 403

6. **Unrestricted Access to Sensitive Business Flows**
   - Mitigation: Rate limiting notes (future implementation)
   - Log sensitive actions (login, account deactivation)

7. **Server-Side Request Forgery (SSRF)**
   - Mitigation: No user-supplied URLs in backend calls
   - Future: If external API calls added, validate and whitelist URLs

8. **Security Misconfiguration**
   - Mitigation: CORS whitelist, Swagger disabled in production
   - Actuator endpoints (if added) require authentication
   - Error messages don't reveal system details

9. **Improper Inventory Management**
   - Mitigation: API versioning (`/api/v1/`), OpenAPI documentation
   - Deprecated endpoints tracked in version history

10. **Unsafe Consumption of APIs**
    - Mitigation: Validate all external API responses (future phase)
    - Circuit breaker for resilience

---

## Observability Strategy

### Structured Logging

**Framework:** structlog with JSON formatting

**Log Format (Production):**
```json
{
  "timestamp": "2026-02-24T12:34:56.789Z",
  "level": "INFO",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "User login successful",
  "user_email": "user@example.com",
  "endpoint": "POST /auth/login",
  "method": "POST",
  "path": "/auth/login",
  "status": 200,
  "response_time_ms": 45,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

**Log Format (Development - Readable):**
```
2026-02-24 12:34:56 [INFO] [550e8400...] User login successful - user_email=user@example.com endpoint=POST /auth/login status=200 response_time_ms=45
```

**Log Levels:**
- **ERROR:** Application errors, exceptions, database failures (always log)
- **WARNING:** Validation failures, slow queries (>100ms), circuit breaker state changes
- **INFO:** Successful authentication, profile updates, health checks
- **DEBUG:** Request/response bodies, SQL queries, token validation details

### Correlation IDs

**Generation:** UUID v4 per incoming HTTP request
**Propagation:**
- Extract from `X-Correlation-Id` request header if present
- Generate new UUID if header missing
- Include in response via `X-Correlation-Id` response header
- Include in all log entries via context variable

**Usage:**
```python
# In middleware
correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
contextvars.set("correlation_id", correlation_id)

# In logging
logger = structlog.get_logger()
logger.info("event", correlation_id=correlation_id, user_email=email)

# In response
response.headers["X-Correlation-Id"] = correlation_id
```

**Tracing:** Allows ops teams to correlate logs across requests for end-to-end debugging

### Health Checks

**Liveness Probe: `/health/live`**
- **Purpose:** Check if app is running
- **Response:** 200 OK (always, as long as app process is alive)
- **Timeout:** < 1 second
- **Response body:**
```json
{
  "status": "alive",
  "timestamp": "2026-02-24T12:34:56.789Z",
  "uptime_seconds": 3600
}
```

**Readiness Probe: `/health/ready`**
- **Purpose:** Check if app is ready to serve traffic
- **Checks:**
  - Database connectivity (execute simple query)
  - Circuit breaker status (not OPEN)
  - Config validation
- **Response:** 200 OK if healthy, 503 Service Unavailable if degraded
- **Timeout:** < 5 seconds
- **Response body:**
```json
{
  "status": "ready",
  "timestamp": "2026-02-24T12:34:56.789Z",
  "dependencies": {
    "database": "healthy",
    "circuit_breaker": "closed"
  }
}
```

### Metrics (Mentioned, Not Implemented in MVP)
- Request count per endpoint
- Request latency (p50, p95, p99)
- Error rate per endpoint
- Circuit breaker state transitions
- Future: Integrate with Prometheus `/metrics` endpoint

### Slow Query Logging

**Threshold:** 100ms (configurable)
**Logged Information:**
- Query text
- Execution time (ms)
- Correlation ID
- Query parameters

---

## Configuration Strategy (12-Factor App)

### Environment-Based Configuration

**Principle:** All config via environment variables; no hardcoded values in code

**Configuration Parameters:**

| Variable | Type | Required | Default | Dev | Prod |
|----------|------|----------|---------|-----|------|
| `ENVIRONMENT` | string | No | development | development | production |
| `SERVICE_PORT` | int | No | 8000 | 8000 | 8000 |
| `DATABASE_URL` | string | Yes (prod) | sqlite:///./dev.db | sqlite | postgresql |
| `JWT_SECRET_KEY` | string | Yes | — (fail if missing) | test_key_32chars | (env var) |
| `JWT_ALGORITHM` | string | No | HS256 | HS256 | HS256 |
| `JWT_EXPIRATION_MINUTES` | int | No | 15 | 15 | 15 |
| `LOG_LEVEL` | string | No | INFO | DEBUG | INFO |
| `CORS_ORIGINS` | string | No | http://localhost:3000 | http://localhost:3000 | https://app.example.com |
| `DATABASE_POOL_MIN` | int | No | 5 | 1 | 5 |
| `DATABASE_POOL_MAX` | int | No | 20 | 5 | 20 |

### Profiles

**Development Profile:**
- Database: SQLite (in-memory or file-based)
- Log level: DEBUG
- Swagger UI: Enabled (`/docs`)
- CORS: Allow localhost
- JWT secret: Test value
- Error responses: Include detailed error messages (safe in dev)

**Production Profile:**
- Database: PostgreSQL (external, managed)
- Log level: INFO
- Swagger UI: Disabled (no `/docs`)
- CORS: Whitelist specific origins
- JWT secret: Required from environment (fail-fast if missing)
- Error responses: Generic messages, details in server logs

### Startup Validation (Fail-Fast)

**Validated on application startup:**
1. Required environment variables present (JWT_SECRET_KEY)
2. DATABASE_URL format valid
3. Database connectivity (test connection)
4. JWT_SECRET_KEY sufficient length (min 32 chars)
5. LOG_LEVEL valid (DEBUG, INFO, WARNING, ERROR)

**Failure:** Application refuses to start, logs error, exits with code 1

### Configuration Initialization

**config.py (Pydantic Settings):**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    service_port: int = 8000
    database_url: str = "sqlite:///./dev.db"
    jwt_secret_key: str  # No default, required
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()

# Startup validation
assert len(settings.jwt_secret_key) >= 32, "JWT_SECRET_KEY too short"
```

---

## Error Handling Strategy

### Exception Hierarchy

```python
AppException (base)
├── ValidationError          → 400 Bad Request
├── AuthenticationError       → 401 Unauthorized
├── AuthorizationError        → 403 Forbidden
├── NotFoundError             → 404 Not Found
├── ConflictError             → 409 Conflict
└── ServiceUnavailableError   → 503 Service Unavailable
```

### Error Response Format

**Standard Response (all errors):**
```json
{
  "status": 400,
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-24T12:34:56.789Z",
  "errors": [
    {"field": "email", "message": "Invalid email format"},
    {"field": "password", "message": "Password too short"}
  ]
}
```

### HTTP Status Code Mapping

| Exception | HTTP Status | Meaning |
|-----------|------------|---------|
| ValidationError | 400 | Client request is malformed or invalid |
| AuthenticationError | 401 | User not authenticated or credentials invalid |
| AuthorizationError | 403 | User authenticated but lacks permissions |
| NotFoundError | 404 | Requested resource does not exist |
| ConflictError | 409 | Request conflicts with system state (e.g., duplicate email) |
| ServiceUnavailableError | 503 | Service temporarily unavailable (circuit open, DB down) |
| Unexpected Exception | 500 | Unexpected server error |

### Global Exception Handler

**Mechanism:** FastAPI exception handlers at application level

**Handler Logic:**
1. Catch all exceptions (unhandled)
2. Extract correlation_id from context
3. Log full stack trace with correlation_id
4. Map exception type to HTTP status
5. Serialize to ErrorResponse DTO (no stack trace in response)
6. Return response with appropriate status code

**Development vs Production:**
- **Development:** Error responses may include `details` field with debug info
- **Production:** Generic messages only, full details in server logs (accessible via correlation_id)

### Logging on Error

**Every exception logged with:**
- Correlation ID
- Full stack trace
- Request context (method, path, user email if authenticated)
- Error-specific context (field name, constraint violated, etc.)

**Example error log:**
```json
{
  "timestamp": "2026-02-24T12:34:56.789Z",
  "level": "ERROR",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Database integrity violation",
  "error_type": "IntegrityError",
  "endpoint": "POST /auth/register",
  "user_email": "user@example.com",
  "constraint": "users.email_active_unique",
  "stack_trace": "..."
}
```

---

## API Design Principles

### RESTful Conventions

**Resource URIs:**
- `/api/v1/auth/register` — POST to register
- `/api/v1/auth/login` — POST to login
- `/api/v1/auth/refresh` — POST to refresh token
- `/api/v1/users/me` — GET current user, PATCH update, DELETE deactivate
- `/api/v1/admin/users` — GET list (ADMIN only)
- `/api/v1/admin/users/{id}/role` — PATCH to change role (ADMIN only)
- `/api/v1/health/live` — GET liveness probe
- `/api/v1/health/ready` — GET readiness probe

### Versioning

**Strategy:** URL path versioning (`/api/v1/`)
- Allows multiple API versions simultaneously
- Clear deprecation path for breaking changes
- Recommended for long-term stability

**Future Versioning:**
- `/api/v2/` introduced for backwards-incompatible changes
- `/api/v1/` maintained for existing clients

### Request Format

**Content-Type:** `application/json` (required for POST/PATCH/DELETE)

**Authentication Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response Format

**Success Response (2xx):**
```json
{
  "data": {
    "id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "USER",
    "created_at": "2026-02-24T12:34:56.789Z"
  }
}
```

**Error Response (4xx, 5xx):**
```json
{
  "status": 400,
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-24T12:34:56.789Z",
  "errors": [...]
}
```

### Pagination

**Query Parameters:**
- `?limit=20&offset=0` — Default limit 20, max 100

**Response Format:**
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### Date/Time Format

**Standard:** ISO 8601 UTC
**Example:** `2026-02-24T12:34:56.789Z`

---

## Database Design

### Entity-Relationship Diagram (Text)

```
┌──────────────────────────────┐
│          users               │
├──────────────────────────────┤
│ id (PK)              integer  │ auto-increment
│ email (UNIQUE)       varchar  │ RFC 5322 format
│ password_hash        varchar  │ BCrypt hash
│ name                 varchar  │ max 100 chars
│ role                 enum     │ USER, ADMIN (default: USER)
│ active               boolean  │ soft delete flag
│ created_at           datetime │ auto-set UTC
│ updated_at           datetime │ auto-set UTC
└──────────────────────────────┘

Indexes:
├─ PRIMARY KEY (id)
├─ UNIQUE (email) WHERE active = true
├─ INDEX (active)
├─ INDEX (role)
└─ INDEX (created_at)
```

### Schema Details

**User Table:**
- **id** — Auto-incrementing primary key
- **email** — RFC 5322 compliant, unique per active user, normalized to lowercase
- **password_hash** — BCrypt hash (never store plain text)
- **name** — User display name, max 100 characters
- **role** — Enum: USER (default) or ADMIN
- **active** — Boolean flag for soft delete (true = active, false = deactivated)
- **created_at** — Timestamp set on insert, UTC
- **updated_at** — Timestamp set on insert and update, UTC

**Constraints:**
- Primary key on `id`
- Unique constraint on `(email, active=true)` to allow deactivated users to reuse email
- NOT NULL on all columns except optional future fields
- Default values: role=USER, active=true, created_at/updated_at=now()

---

## Circuit Breaker Pattern

### Implementation

**Purpose:** Prevent cascading failures from external service calls (future phase)

**States:**
- **CLOSED** — Normal operation, requests pass through
- **OPEN** — Failure threshold exceeded, requests fail immediately with 503
- **HALF_OPEN** — Recovery probe, limited requests allowed

**Configuration (Configurable):**
- `failure_threshold` — Consecutive failures to trigger open (default: 5)
- `timeout` — Duration before transitioning to half-open (default: 30 seconds)
- `half_open_limit` — Requests allowed in half-open state (default: 1)

**Transitions:**
- CLOSED → OPEN: After 5 consecutive failures
- OPEN → HALF_OPEN: After 30 second timeout
- HALF_OPEN → CLOSED: After successful request
- HALF_OPEN → OPEN: After failed request

**Logging:**
- State transitions logged with timestamp
- Correlation ID included in logs

**Health Check Integration:**
- Circuit breaker state visible in `/health/ready` response
- If any circuit is OPEN, readiness returns 503

---

## Summary

This layered monolith architecture provides:
- **Clarity:** Distinct responsibilities per layer
- **Security:** JWT auth, BCrypt hashing, input validation, SQL injection prevention
- **Observability:** Structured logging with correlation IDs, health checks
- **Reliability:** Graceful error handling, circuit breaker resilience (future)
- **Scalability:** Stateless design supports horizontal scaling
- **Maintainability:** Clear component boundaries, easy testing, configuration management

All design decisions prioritize security, observability, and operational readiness.
