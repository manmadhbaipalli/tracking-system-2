# Auth Service App - Technical Design

## Approach

This is a **greenfield FastAPI authentication service** following modern Python web development patterns. The architecture uses a layered approach with clear separation of concerns:

1. **API Layer** - FastAPI routers handling HTTP requests/responses
2. **Business Logic Layer** - CRUD operations and service logic
3. **Data Access Layer** - SQLAlchemy models and database operations
4. **Cross-cutting Concerns** - Security, logging, configuration, exception handling

The design emphasizes:
- **Type Safety** - Comprehensive use of type hints and Pydantic validation
- **Async/Await** - Non-blocking I/O throughout the application stack
- **Dependency Injection** - FastAPI's DI system for testability and modularity
- **Security Best Practices** - JWT tokens, bcrypt password hashing, input validation
- **Observability** - Structured JSON logging with correlation IDs
- **Resilience** - Circuit breaker pattern for external dependencies

## Detailed Changes

### Core Infrastructure (`app/core/`)

**`app/core/config.py`**
- Pydantic `BaseSettings` class for type-safe configuration
- Environment variables: `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- Development vs production database URL handling (SQLite/PostgreSQL)
- Logging level and format configuration

**`app/core/security.py`**
- Password hashing with bcrypt (12+ rounds)
- JWT token creation with configurable expiration
- Token verification with proper exception handling
- Password verification utility functions

**`app/core/logging.py`**
- JSON structured logging setup
- Correlation ID middleware for request tracing
- Log level configuration based on environment
- Sensitive data filtering (passwords, tokens)

**`app/core/exceptions.py`**
- Custom exception classes: `AuthenticationError`, `UserExistsError`
- Global FastAPI exception handlers
- Standardized error response format: `{"detail": "message", "error_code": "CODE"}`
- HTTP status code mapping for different exception types

### Data Layer (`app/models/`, `app/schemas/`, `app/crud/`)

**`app/models/user.py`**
- SQLAlchemy 2.0 async model
- Fields: `id` (UUID), `email` (unique), `hashed_password`, `created_at`, `is_active`
- Proper table name and constraints
- Index on email for performance

**`app/schemas/user.py`**
- `UserCreate`: email validation, password strength requirements
- `UserLogin`: email and password fields
- `UserResponse`: safe user data (no password), `from_orm` support
- Email validation with regex pattern

**`app/schemas/token.py`**
- `Token`: access_token (str), token_type (str, default "bearer")
- `TokenData`: username/email for token payload

**`app/crud/user.py`**
- `create_user()`: Hash password, create user, handle duplicates
- `get_user_by_email()`: Query user by email with error handling
- `authenticate_user()`: Verify email/password combination
- All functions use async/await with proper session handling

### API Layer (`app/api/`)

**`app/api/deps.py`**
- `get_db()`: Database session dependency with proper cleanup
- `get_current_user()`: JWT token validation and user extraction
- `get_current_active_user()`: Active user verification
- Circuit breaker decorator for database operations

**`app/api/v1/auth.py`**
- `POST /register`: User registration with validation
  - Email uniqueness check
  - Password hashing
  - Success response with user data
- `POST /login`: User authentication with JWT
  - Credential validation
  - Token generation with expiration
  - Rate limiting consideration

**`app/api/v1/users.py`**
- `GET /users/me`: Current user profile endpoint
  - Authentication required
  - Returns user data without sensitive fields
  - Proper error handling for invalid tokens

**`app/main.py`**
- FastAPI application factory
- CORS middleware configuration
- Global exception handler registration
- API router mounting (`/api/v1/`)
- Health check endpoint (`/health`)
- OpenAPI documentation at `/docs`

### Database Layer (`app/db/`)

**`app/db/session.py`**
- SQLAlchemy 2.0 async engine setup
- Session factory with proper async context
- Database URL from configuration
- Connection pooling configuration

**`app/db/base.py`**
- Import all models for Alembic autogenerate
- Base class exports for consistent model inheritance

### Configuration Files

**`requirements.txt`**
```
fastapi[all]==0.104.1
sqlalchemy[asyncio]==2.0.23
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
circuitbreaker==1.4.0
```

**`requirements-dev.txt`**
```
-r requirements.txt
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
black==23.11.0
isort==5.12.0
mypy==1.7.1
coverage==7.3.2
```

**`pyproject.toml`**
- Black configuration (line-length=88)
- isort configuration (profile="black")
- mypy configuration (strict mode, ignore missing imports)

**`alembic.ini`**
- Database URL from environment
- Migration file template
- Timezone-aware timestamps

**`.env.example`**
```
DATABASE_URL=sqlite:///./auth_service.db
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL=INFO
```

## Interfaces

### API Contracts

**Authentication Endpoints**
```python
POST /api/v1/auth/register
Request: {"email": "user@example.com", "password": "secure123"}
Response: {"id": "uuid", "email": "user@example.com", "created_at": "2024-01-01T00:00:00Z"}

POST /api/v1/auth/login
Request: {"email": "user@example.com", "password": "secure123"}
Response: {"access_token": "jwt-token", "token_type": "bearer"}

GET /api/v1/users/me
Headers: {"Authorization": "Bearer jwt-token"}
Response: {"id": "uuid", "email": "user@example.com", "created_at": "2024-01-01T00:00:00Z"}
```

**Error Response Format**
```python
{
    "detail": "Human readable error message",
    "error_code": "MACHINE_READABLE_CODE"
}
```

### Internal Interfaces

**CRUD Functions**
```python
async def create_user(db: AsyncSession, user: UserCreate) -> User
async def get_user_by_email(db: AsyncSession, email: str) -> User | None
async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None
```

**Security Functions**
```python
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str
def verify_token(token: str) -> TokenData
def get_password_hash(password: str) -> str
def verify_password(plain_password: str, hashed_password: str) -> bool
```

**Dependencies**
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]
async def get_current_user(db: AsyncSession, token: str) -> User
```

## Trade-offs

### Architecture Decisions

**SQLAlchemy 2.0 vs 1.x**
- ✅ Chosen: 2.0 for modern async support and better type hints
- ❌ Alternative: 1.x for more mature ecosystem
- **Rationale**: Future-proof choice, better async performance

**JWT vs Session-based Auth**
- ✅ Chosen: JWT for stateless authentication
- ❌ Alternative: Session cookies for simpler implementation
- **Rationale**: Better for API-first design, scalability, mobile clients

**SQLite vs PostgreSQL for Development**
- ✅ Chosen: SQLite for dev, PostgreSQL for production
- ❌ Alternative: PostgreSQL everywhere
- **Rationale**: Faster local development, production parity where needed

**Async vs Sync**
- ✅ Chosen: Async throughout the application
- ❌ Alternative: Sync for simpler code
- **Rationale**: Better performance under load, FastAPI best practices

### Security Trade-offs

**Password Storage**
- ✅ Chosen: bcrypt with 12 rounds
- ❌ Alternative: Argon2 (more secure but complex)
- **Rationale**: Industry standard, well-tested, sufficient for most use cases

**Token Expiration**
- ✅ Chosen: 30-minute access tokens, no refresh tokens initially
- ❌ Alternative: Longer-lived tokens or refresh token flow
- **Rationale**: Simpler implementation, good security baseline

### Performance Trade-offs

**Circuit Breaker Pattern**
- ✅ Chosen: Applied to database operations
- ❌ Alternative: Simple retry logic
- **Rationale**: Better resilience under load, fail-fast behavior

**Database Connection Pooling**
- ✅ Chosen: SQLAlchemy's built-in pooling
- ❌ Alternative: External connection pooler
- **Rationale**: Simpler setup, sufficient for moderate load

## Open Questions

### For Implementation Agent

1. **Rate Limiting**: Should we implement rate limiting on login attempts? If so, what strategy (IP-based, user-based, Redis vs in-memory)?

2. **User Activation**: Do we need email verification for user registration, or is immediate activation acceptable?

3. **Password Policies**: Should we enforce specific password complexity requirements beyond minimum length?

4. **Logging Sensitivity**: What specific fields should be filtered from logs beyond passwords and tokens (email addresses, user IDs)?

5. **Health Check Details**: Should the `/health` endpoint check database connectivity or just return a simple 200 OK?

6. **CORS Configuration**: What specific origins should be allowed, or should we use wildcard for development?

7. **Circuit Breaker Thresholds**: What failure rate and timeout values should trigger the circuit breaker for database operations?

8. **Migration Strategy**: Should we create an initial migration with the User model, or let Alembic generate it automatically?

### Recommendations for Implementation

- Start with basic password validation (minimum 8 characters) and enhance later
- Use in-memory rate limiting for simplicity (can be upgraded to Redis later)
- Skip email verification initially (add as future enhancement)
- Allow all origins in CORS for development, require configuration for production
- Use conservative circuit breaker settings (5 failures in 60 seconds, 30-second timeout)
- Create explicit initial migration for better control over database schema