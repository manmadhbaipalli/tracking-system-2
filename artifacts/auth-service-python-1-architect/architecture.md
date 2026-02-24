# Architecture: Auth Service Python 1

## Architecture Overview

**Style:** Layered Monolith
**Rationale:** FastAPI authentication service with clear separation of concerns through controller, service, and repository layers. This architecture provides simplicity, maintainability, and is well-suited for the authentication domain with straightforward CRUD operations and business logic.

### Component Diagram (Text)

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Router Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │AuthRouter    │  │UserRouter     │  │HealthRouter       │  │
│  │/auth/*       │  │/users/*       │  │ /health/*         │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘  │
├─────────┼─────────────────┼─────────────────────┼─────────────┤
│         │          Service Layer                │             │
│  ┌──────┴───────┐  ┌──────┴────────┐  ┌────────┴─────────┐  │
│  │ AuthService  │  │ UserService    │  │ HealthService    │  │
│  └──────┬───────┘  └──────┬────────┘  └────────┬─────────┘  │
├─────────┼─────────────────┼─────────────────────┼─────────────┤
│         │       Repository Layer                │             │
│  ┌──────┴───────┐  ┌──────┴────────┐  ┌────────┴─────────┐  │
│  │ UserRepo     │  │ RequestLogRepo │  │ CircuitBreaker   │  │
│  └──────┬───────┘  └──────┬────────┘  └────────┬─────────┘  │
├─────────┼─────────────────┼─────────────────────┼─────────────┤
│                   SQLAlchemy + PostgreSQL                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Decisions

| Category | Decision | Rationale |
|----------|----------|-----------|
| Language | Python 3.12 | Modern Python with latest performance improvements, type hints |
| Framework | FastAPI 0.100+ | Async support, automatic API docs, Pydantic validation, high performance |
| Database | PostgreSQL 16 (prod), SQLite (dev) | ACID compliance, JSON support, mature ecosystem |
| ORM | SQLAlchemy 2.0+ with async | Type-safe ORM with async support for FastAPI |
| Authentication | JWT access tokens | Stateless, scalable, industry standard |
| API Docs | FastAPI auto-generated OpenAPI | Built-in Swagger/ReDoc, zero configuration |
| Migration | Alembic | Standard SQLAlchemy migration tool |
| Logging | structlog + JSON formatter | Structured logging with correlation IDs |
| Password Hashing | BCrypt (passlib) | Industry standard, configurable cost factor |
| Validation | Pydantic v2 | Built into FastAPI, excellent performance and validation |
| HTTP Client | httpx (for circuit breaker) | Async HTTP client for external dependencies |
| Build Tool | pip + requirements.txt | Standard Python dependency management |

---

## Component Design

### Router Layer (app/routers/)
- **Purpose:** HTTP request handling, input validation via Pydantic, response serialization
- **Dependencies:** Service layer, authentication dependencies
- **Public API:** REST endpoints under `/api/v1/`

### Service Layer (app/services/)
- **Purpose:** Business logic, transaction management, authentication rules
- **Dependencies:** Repository layer, security utilities, circuit breaker
- **Public API:** Service methods called by routers

### Repository Layer (app/repositories/)
- **Purpose:** Data access, CRUD operations, query optimization
- **Dependencies:** SQLAlchemy models, database session
- **Public API:** Repository classes with async methods

### Security Layer (app/security.py)
- **Purpose:** JWT token generation/validation, password hashing, auth dependencies
- **Dependencies:** JWT library, passlib for BCrypt
- **Public API:** Auth dependencies, token utilities

---

## Data Flow

```
Client → Router → Pydantic Schema → Service → Repository → SQLAlchemy → Database
         (JSON)    (Validation)      (Business)  (Data)      (ORM)
         ←  JSON ←    Schema    ←    DTO     ←    Model   ← Query Results ←
```

---

## Security Architecture

### Authentication
- Method: JWT Bearer tokens
- Token lifetime: 86400 seconds (24 hours, configurable via JWT_EXPIRATION_SECONDS)
- Token structure: `{ "sub": user_id, "email": "user@example.com", "role": "USER", "iat": ..., "exp": ... }`
- Password hashing: BCrypt (cost factor 12)
- Token signing: HS256 algorithm with configurable secret

### Authorization (Endpoint Access Matrix)

| Endpoint Pattern | Public | USER | ADMIN |
|------------------|--------|------|-------|
| POST /api/v1/auth/register | Yes | — | — |
| POST /api/v1/auth/login | Yes | — | — |
| GET /api/v1/users/me | — | Yes | Yes |
| PUT /api/v1/users/me | — | Yes | Yes |
| PUT /api/v1/users/me/password | — | Yes | Yes |
| GET /api/v1/admin/users | — | — | Yes |
| PUT /api/v1/admin/users/{id}/role | — | — | Yes |
| PUT /api/v1/admin/users/{id}/status | — | — | Yes |
| GET /health/live | Yes | — | — |
| GET /health/ready | Yes | — | — |
| GET /docs | Yes | — | — |

### OWASP API Top 10 Mitigations
1. **BOLA** → Verify resource ownership in service layer (user can only access own profile)
2. **Broken Auth** → JWT validation middleware, BCrypt cost 12, secure token generation
3. **BOPLA** → Pydantic schema filtering (never expose password_hash in responses)
4. **Unrestricted Resources** → Pagination limits (default 20, max 100 items)
5. **BFLA** → Role-based endpoint access via FastAPI dependencies
6. **Sensitive Flows** → Rate limiting for failed login attempts (5 per hour per email)
7. **SSRF** → No user-supplied URLs in backend calls
8. **Security Misconfig** → CORS whitelist, security headers middleware
9. **Improper Inventory** → API versioning (/api/v1/), comprehensive OpenAPI docs
10. **Unsafe Consumption** → Input validation on all external data

---

## Observability Strategy

### Logging
- Format: Structured JSON (production), readable format (development)
- Framework: structlog with JSON processor for production
- Log Levels: ERROR (failures), WARN (degradation), INFO (business events), DEBUG (troubleshooting)
- **Never log:** passwords, JWT tokens, password hashes, PII

### Correlation IDs
- Generated: UUID4 for each incoming request via middleware
- Propagated via: `X-Correlation-Id` header (both request and response)
- Included in: ALL log statements via contextvars integration

### Health Checks
- **Liveness:** `GET /health/live` - Simple 200 OK (app is running)
- **Readiness:** `GET /health/ready` - Includes database connectivity and circuit breaker status
- Response format: `{"status": "healthy", "timestamp": "...", "checks": {...}}`

### Request Logging
- All HTTP requests/responses logged with correlation ID
- Performance metrics: request duration, status code
- Authentication events: login success/failure, token validation
- Database operations: query performance, connection pool status

---

## Configuration Strategy (12-Factor App)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| DATABASE_URL | Database connection string | No | sqlite:///./dev.db |
| JWT_SECRET_KEY | JWT signing key | Yes (prod) | — |
| JWT_EXPIRATION_SECONDS | Token lifetime | No | 86400 |
| CORS_ORIGINS | Comma-separated allowed origins | No | http://localhost:3000,http://localhost:3001 |
| LOG_LEVEL | Logging level | No | INFO |
| HOST | Server host | No | 0.0.0.0 |
| PORT | Server port | No | 8000 |
| ENVIRONMENT | Runtime environment | No | development |
| BCRYPT_ROUNDS | BCrypt cost factor | No | 12 |
| RATE_LIMIT_LOGIN_ATTEMPTS | Failed login limit per hour | No | 5 |
| CIRCUIT_BREAKER_FAILURE_THRESHOLD | DB failures before circuit opens | No | 5 |
| CIRCUIT_BREAKER_TIMEOUT_SECONDS | Circuit breaker timeout | No | 60 |

---

## Circuit Breaker Strategy

### Database Circuit Breaker
- **Purpose:** Prevent cascading failures during database outages
- **Implementation:** Custom decorator using httpx for async operations
- **States:** CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
- **Thresholds:** 5 consecutive failures opens circuit, 60-second timeout
- **Monitoring:** Circuit breaker status included in readiness health check

### Configuration
- Failure threshold: 5 consecutive database connection failures
- Timeout duration: 60 seconds before attempting recovery
- Half-open test: Single request to test database recovery
- Fallback behavior: Return 503 Service Unavailable with meaningful error

---

## Database Design

### Entity Relationships
```
User (1) ←→ (N) RequestLog (audit trail)
User (1) ←→ (N) AuthToken (optional token blacklist)
User (1) ←→ (N) User (self-reference for audit: created_by, updated_by)
```

### Key Indexes
- `users.email` (unique index for login lookups)
- `users.active` (for user listing)
- `request_logs.correlation_id` (for request tracing)
- `request_logs.created_at` (for log cleanup)
- `auth_tokens.token_hash` (if implementing token blacklist)

---

## Error Handling Strategy

### Exception Hierarchy
- `AuthServiceException` (base exception)
  - `AuthenticationException` → 401 Unauthorized
  - `AuthorizationException` → 403 Forbidden
  - `ConflictException` → 409 Conflict (email exists)
  - `NotFoundException` → 404 Not Found
  - `ValidationException` → 422 Unprocessable Entity
  - `ServiceUnavailableException` → 503 Service Unavailable (circuit breaker)

### Global Exception Handler
```json
{
  "status_code": 400,
  "error": "Bad Request",
  "message": "Validation failed",
  "details": ["Email is required", "Password must be at least 8 characters"],
  "correlation_id": "12345678-1234-1234-1234-123456789012",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

### Error Response Standards
- Always include correlation_id for tracing
- Field-specific validation errors in details array
- Generic error messages in production (no stack traces)
- Consistent HTTP status codes across all endpoints

---

## API Design Principles

### RESTful Conventions
- Resource-based URLs: `/api/v1/users/{id}`
- HTTP methods: GET (read), POST (create), PUT (update), DELETE (remove)
- Status codes: 200 (OK), 201 (Created), 204 (No Content), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict), 422 (Validation Error), 503 (Service Unavailable)

### Versioning
- URL-based versioning: `/api/v1/`
- Backward compatibility maintained within major versions
- OpenAPI spec version matches API version

### Pagination
- Query parameters: `?limit=20&offset=0`
- Response envelope: `{"items": [...], "total": 100, "limit": 20, "offset": 0}`
- Default limit: 20, maximum limit: 100

### Request/Response Format
- Content-Type: `application/json`
- Date format: ISO 8601 UTC (`2026-02-24T10:30:00Z`)
- ID format: Integer primary keys
- Boolean values: `true`/`false` (not 1/0)