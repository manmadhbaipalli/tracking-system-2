# FastAPI Application Design

## Approach

This design follows a layered architecture pattern with clear separation of concerns:

1. **API Layer**: FastAPI routers handling HTTP requests/responses
2. **Service Layer**: Business logic and orchestration
3. **Data Layer**: SQLAlchemy models and database operations
4. **Core Utilities**: Cross-cutting concerns (auth, logging, config)

The architecture prioritizes:
- **Security**: JWT authentication, password hashing, input validation
- **Reliability**: Circuit breaker pattern, centralized error handling
- **Observability**: Structured logging throughout the application
- **Maintainability**: Clear module boundaries and dependency injection

## Detailed Changes

### Configuration & Dependencies

**requirements.txt** - Core dependencies:
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `sqlalchemy>=2.0.0` - ORM
- `python-jose[cryptography]>=3.3.0` - JWT handling
- `passlib[bcrypt]>=1.7.4` - Password hashing
- `circuitbreaker>=1.4.0` - Circuit breaker pattern
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support

**pyproject.toml** - Project metadata and tool configuration:
- Black formatter settings (line length 88)
- mypy type checking configuration
- pytest configuration for async tests

### Core Infrastructure

**app/database.py** - Database setup:
- SQLAlchemy engine with SQLite
- Async session factory
- Database initialization function

**app/core/config.py** - Application configuration:
- Pydantic BaseSettings for environment variables
- JWT secret key, database URL, logging level
- Development/production configuration separation

**app/core/security.py** - Security utilities:
- Password hashing with bcrypt
- JWT token creation and validation
- Token expiration handling (24 hours access, 30 days refresh)

**app/core/logging.py** - Logging setup:
- Structured JSON logging format
- Request ID correlation
- Configurable log levels

**app/core/exceptions.py** - Exception handling:
- Custom exception classes (AuthenticationError, ValidationError)
- Global exception handlers for consistent error responses
- HTTP status code mapping

### Data Models

**app/models/user.py** - User SQLAlchemy model:
```python
class User(Base):
    __tablename__ = "users"

    id: int (primary key)
    email: str (unique, indexed)
    hashed_password: str
    is_active: bool (default True)
    created_at: datetime
    updated_at: datetime
```

**app/schemas/user.py** - Pydantic schemas:
- `UserCreate` - Registration input (email, password)
- `UserLogin` - Login input (email, password)
- `UserResponse` - User data response (id, email, is_active, created_at)
- `Token` - JWT token response (access_token, token_type, expires_in)

### Business Logic

**app/services/auth.py** - Authentication service:
- `register_user()` - Create new user with hashed password
- `authenticate_user()` - Verify credentials and return user
- `create_access_token()` - Generate JWT token
- Email uniqueness validation
- Password strength requirements

**app/services/circuit_breaker.py** - Circuit breaker service:
- Decorator for protecting external calls
- Configurable failure threshold (5 failures in 60 seconds)
- Recovery timeout (30 seconds)
- Metrics collection for monitoring

### API Layer

**app/api/deps.py** - Dependency injection:
- `get_db()` - Database session dependency
- `get_current_user()` - JWT authentication dependency
- Error handling for invalid tokens

**app/api/v1/endpoints/auth.py** - Authentication endpoints:
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- Input validation, error responses, success responses

**app/main.py** - FastAPI application:
- App initialization with metadata
- CORS middleware for development
- Exception handler registration
- Router registration (/api/v1)
- Automatic OpenAPI documentation

## Interfaces

### Authentication API Contract

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
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}

Response (400):
{
  "detail": "Email already registered"
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
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}

Response (401):
{
  "detail": "Invalid credentials"
}
```

### Service Layer Interfaces

**AuthService Methods**:
```python
async def register_user(db: Session, user_data: UserCreate) -> User
async def authenticate_user(db: Session, email: str, password: str) -> User | None
def create_access_token(data: dict) -> str
```

**CircuitBreaker Decorator**:
```python
@circuit_breaker(failure_threshold=5, recovery_timeout=30)
async def external_api_call() -> dict
```

## Trade-offs

### Database Choice: SQLite vs PostgreSQL
**Chosen**: SQLite for development simplicity
- **Pros**: No setup required, file-based, good for development
- **Cons**: Limited concurrency, not suitable for production scale
- **Migration Path**: Easy upgrade to PostgreSQL with minimal code changes

### Authentication: JWT vs Sessions
**Chosen**: JWT tokens
- **Pros**: Stateless, scalable, works with mobile apps
- **Cons**: Cannot revoke tokens easily, larger payload than session IDs
- **Mitigation**: Short token expiration (24 hours) with refresh mechanism

### Password Storage: bcrypt vs Argon2
**Chosen**: bcrypt with passlib
- **Pros**: Well-established, good library support, configurable cost
- **Cons**: Slightly slower than newer algorithms
- **Rationale**: Mature ecosystem and sufficient security for current needs

### Circuit Breaker: Custom vs Library
**Chosen**: `circuitbreaker` library
- **Pros**: Battle-tested, configurable, minimal code
- **Cons**: External dependency, less control over implementation
- **Rationale**: Focus on business logic rather than infrastructure

## Open Questions

### Implementation Decisions for the Next Phase

1. **Password Requirements**:
   - Minimum length requirement (suggest 8 characters)
   - Complexity requirements (numbers, special chars)?
   - Should implement basic validation or comprehensive policy?

2. **Token Refresh Strategy**:
   - Implement refresh tokens or rely on short-lived access tokens?
   - Auto-refresh on API calls or require explicit refresh endpoint?

3. **User Activation**:
   - Email verification required for new accounts?
   - Admin approval process needed?
   - For now, users are active by default

4. **Rate Limiting**:
   - Implement rate limiting on auth endpoints?
   - Use Redis or in-memory storage?
   - Defer to deployment/infrastructure layer?

5. **Logging Sensitivity**:
   - What level of user data should be logged?
   - Mask passwords/tokens in logs (recommended)
   - Log successful authentications for audit trail?

6. **Database Migration Strategy**:
   - Use Alembic for schema migrations?
   - Manual table creation for initial setup?
   - Recommend starting simple with SQLAlchemy create_all()

These decisions can be made during implementation based on specific requirements and time constraints.