# FastAPI Application - Design Document

## Approach

This design creates a production-ready FastAPI application with authentication, logging, error handling, and circuit breaker patterns. The architecture follows a layered approach:

1. **Presentation Layer**: FastAPI routers with endpoint definitions
2. **Business Logic Layer**: Service modules for auth, circuit breaker functionality
3. **Data Layer**: SQLAlchemy models and database session management
4. **Cross-Cutting Concerns**: Middleware for logging and exception handling
5. **Configuration & Utilities**: Environment-based config, custom exceptions, logging setup

### Key Design Decisions

1. **Middleware-Based Logging**: Request/response logging implemented as middleware for clean separation of concerns, with unique request IDs for correlation across async boundaries
2. **Centralized Exception Handling**: Single exception handler middleware converts all exceptions to consistent JSON responses
3. **Dependency Injection**: FastAPI's Depends() used for session injection, ensuring proper resource cleanup
4. **Circuit Breaker as Wrapper**: pybreaker wrapped in a custom decorator for easy application to external API calls
5. **Environment-Based Config**: Settings for dev/test/prod environments with sensible defaults

---

## Detailed Changes

### 1. Core Application Setup

#### `app/__init__.py`
- Empty file to mark app as a Python package

#### `app/config.py`
Defines configuration settings per environment (dev, test, prod):
- Database URL (SQLite for dev/test, PostgreSQL for prod)
- JWT secret key (from env variables, defaults to 'secret' in dev)
- JWT algorithm (HS256)
- Token expiry time (24 hours)
- Debug mode (True in dev, False in prod)
- Environment name

#### `app/db.py`
Database connection and session management:
- SQLAlchemy engine creation based on config
- SessionLocal factory for creating database sessions
- Base declarative class for all models
- get_db() dependency function for FastAPI route injection

#### `app/main.py`
FastAPI application initialization:
- Create FastAPI app instance with title, description, version
- Register all middleware (logging, exception handling)
- Register auth router
- Health check endpoint (GET /)
- Automatic Swagger/OpenAPI docs at /docs

### 2. Authentication Module

#### `app/auth/models.py`
SQLAlchemy User model:
- id (Integer, Primary Key)
- email (String, Unique, Not Null)
- hashed_password (String, Not Null)
- created_at (DateTime, Default: current time)

#### `app/auth/schemas.py`
Pydantic schemas for request/response validation:
- `UserRegister`: email, password
- `UserLogin`: email, password
- `UserResponse`: id, email, created_at
- `TokenResponse`: access_token, token_type

#### `app/auth/service.py`
Business logic for authentication:
- `hash_password(password: str) -> str`: Bcrypt password hashing
- `verify_password(password: str, hashed: str) -> bool`: Password verification
- `create_access_token(user_id: int) -> str`: JWT token generation with exp claim
- `verify_token(token: str) -> int`: JWT token verification, returns user_id
- `register_user(email: str, password: str, db) -> User`: Create new user, handle duplicates
- `login_user(email: str, password: str, db) -> User`: Validate credentials, return user

#### `app/auth/router.py`
FastAPI router for auth endpoints:
- `POST /api/v1/auth/register`: Register new user, return UserResponse
- `POST /api/v1/auth/login`: Login user, return TokenResponse with JWT

### 3. Middleware & Exception Handling

#### `app/middleware/logging.py`
Request/response logging middleware:
- Generate unique request ID (UUID) per request
- Log method, path, query params
- Measure response time
- Log response status code and time
- Store request ID in request state for correlation

#### `app/middleware/exception.py`
Global exception handler middleware:
- Catch all exceptions at application level
- Convert exceptions to JSON error responses
- Return appropriate HTTP status codes
- Include error message and request ID in response

### 4. Circuit Breaker

#### `app/circuit_breaker/breaker.py`
Circuit breaker wrapper around pybreaker:
- `create_breaker(name: str, **kwargs)`: Factory function to create breaker with defaults
- `breaker_decorator`: Decorator to apply circuit breaker to async functions
- Handles: open/closed/half-open states, fail_max threshold, reset_timeout
- Example usage: Apply to external API calls that might fail

### 5. Utilities

#### `app/utils/exceptions.py`
Custom exception classes:
- `AppException`: Base exception with status_code, message
- `ValidationError`: 400 Bad Request
- `AuthenticationError`: 401 Unauthorized
- `NotFoundError`: 404 Not Found
- `ConflictError`: 409 Conflict (duplicate email)
- `ExternalServiceError`: 503 Service Unavailable (circuit breaker open)

#### `app/utils/logging.py`
Logging configuration:
- Setup root logger with StreamHandler
- Format: `[%(asctime)s] %(levelname)s [%(name)s] %(message)s`
- Log level: DEBUG in dev, INFO in prod
- Function to get logger by module name

### 6. Configuration Files

#### `requirements.txt`
Dependencies:
- fastapi>=0.104.0
- uvicorn>=0.24.0
- sqlalchemy>=2.0.0
- pydantic>=2.0.0
- pydantic-settings>=2.0.0
- pyjwt>=2.8.0
- python-dotenv>=1.0.0
- pybreaker>=1.4.0
- bcrypt>=4.1.0
- pytest>=7.4.0
- httpx>=0.25.0
- pytest-asyncio>=0.21.0

#### `pytest.ini`
Pytest configuration:
- asyncio_mode = auto (for async test support)
- testpaths = tests
- python_files = test_*.py

#### `.env.example`
Environment variables template:
- DATABASE_URL (optional, defaults to SQLite)
- JWT_SECRET_KEY (optional, defaults to 'secret' in dev)
- ENVIRONMENT (dev, test, prod)

---

## Interfaces

### Authentication Endpoints

**POST /api/v1/auth/register**
```json
Request:
{
  "email": "user@example.com",
  "password": "secure_password"
}

Response (201):
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00"
}

Error (409 - Duplicate):
{
  "detail": "Email already registered",
  "status_code": 409,
  "request_id": "uuid-here"
}
```

**POST /api/v1/auth/login**
```json
Request:
{
  "email": "user@example.com",
  "password": "secure_password"
}

Response (200):
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}

Error (401 - Invalid credentials):
{
  "detail": "Invalid email or password",
  "status_code": 401,
  "request_id": "uuid-here"
}
```

### Service Function Signatures

**AuthService.register_user**
```python
def register_user(
    email: str,
    password: str,
    db: Session
) -> User:
    # Raises ConflictError if email already exists
    # Returns User model instance
```

**AuthService.login_user**
```python
def login_user(
    email: str,
    password: str,
    db: Session
) -> User:
    # Raises AuthenticationError if invalid credentials
    # Returns User model instance
```

**AuthService.create_access_token**
```python
def create_access_token(user_id: int) -> str:
    # Returns JWT token valid for 24 hours
    # Token includes: user_id, exp, iat claims
```

---

## Trade-offs

### 1. In-Memory Logging vs. Centralized Log Aggregation
**Choice**: In-memory logging to stdout
**Trade-off**: Simpler setup, but doesn't scale to multiple instances without external aggregation (ELK, Splunk, etc.)
**Rationale**: Sufficient for initial greenfield project, can be extended later

### 2. SQLite vs. PostgreSQL for Dev
**Choice**: SQLite for dev/test, PostgreSQL option for prod
**Trade-off**: SQLite is not concurrent-safe, but fine for single-process development
**Rationale**: Zero setup overhead, can be swapped at runtime via DATABASE_URL

### 3. JWT vs. Session-Based Authentication
**Choice**: JWT tokens
**Trade-off**: Stateless but can't revoke tokens without external storage
**Rationale**: Simpler for distributed systems, aligns with API-first design

### 4. Circuit Breaker as Decorator vs. Service Layer
**Choice**: Decorator applied to functions
**Trade-off**: Explicit application to each function vs. implicit in service layer
**Rationale**: More control and flexibility for different failure thresholds per endpoint

### 5. Middleware-Based Logging vs. Explicit Logging
**Choice**: Middleware for request/response, explicit logging in services
**Trade-off**: Cleaner separation but less granular control
**Rationale**: Reduces boilerplate, follows FastAPI best practices

---

## Open Questions for Implementation Phase

1. **Database Initialization**: Should `app/db.py` auto-create tables on startup? Or require explicit migration step?
   - **Decision needed**: `Base.metadata.create_all(engine)` vs. Alembic migrations
   - **Recommendation**: Auto-create for dev/test, migrations for prod

2. **Request Timeout**: Should there be a global request timeout? Currently, no timeout is set.
   - **Decision needed**: Add timeout configuration?
   - **Recommendation**: Add optional TIMEOUT_SECONDS to config

3. **Password Complexity**: Currently, any password is accepted. Should we validate length/complexity?
   - **Decision needed**: Add validation rules?
   - **Recommendation**: Not in MVP, can add later

4. **CORS Configuration**: Currently no CORS middleware. Should we add it?
   - **Decision needed**: Add CORS support?
   - **Recommendation**: Not needed for internal API, can add if frontend is separate

5. **Logging Sensitive Data**: Should auth requests be logged? Currently they will be (email visible).
   - **Decision needed**: Redact sensitive fields from logs?
   - **Recommendation**: Redact password, log email for audit trail

---

## Performance Considerations

1. **Database Indexing**: Email field should be indexed (it's unique, so automatic)
2. **JWT Verification**: Lightweight, no database lookup needed
3. **Password Hashing**: bcrypt is intentionally slow (security), acceptable for registration/login
4. **Request ID Generation**: UUID4 generation is negligible cost
5. **Logging**: Async logging would improve performance, but not critical for initial version

---

## Security Considerations

1. **Password Storage**: bcrypt with default cost factor (12)
2. **JWT Secret**: Must be set via environment variable in production
3. **Token Expiry**: 24 hours (1440 minutes)
4. **HTTPS**: Should be enforced in production (via load balancer/reverse proxy)
5. **SQL Injection**: SQLAlchemy ORM prevents this by default
6. **Error Messages**: Generic error responses don't leak information (no "email not found" vs "wrong password")

---

## Testing Strategy

**Unit Tests** (`test_auth.py`):
- test_register_user_success
- test_register_user_duplicate_email
- test_login_user_success
- test_login_user_invalid_email
- test_login_user_invalid_password
- test_password_hashing
- test_token_creation_and_verification

**Integration Tests** (`test_auth.py`):
- test_register_endpoint_201
- test_register_endpoint_409_duplicate
- test_login_endpoint_200
- test_login_endpoint_401_invalid

**Logging Tests** (`test_logging.py`):
- test_request_id_generated
- test_logging_output_format
- test_request_response_logged

**Circuit Breaker Tests** (`test_circuit_breaker.py`):
- test_breaker_closed_success
- test_breaker_opens_after_threshold
- test_breaker_half_open_resets
- test_breaker_open_fails_fast

**Fixture Setup** (`conftest.py`):
- test_db: In-memory SQLite database
- test_client: FastAPI TestClient
- sample_user: Pre-populated test user
- monkeypatch: Pytest built-in for mocking

---

## Deployment Notes

1. **Environment Variables**: Set JWT_SECRET_KEY, DATABASE_URL in production
2. **Logging**: Redirect stdout to centralized log aggregation (CloudWatch, Datadog, etc.)
3. **Database Migration**: Run Alembic or equivalent before deploying
4. **Health Checks**: GET / endpoint for load balancer
5. **Rate Limiting**: Not implemented, can be added via middleware if needed
