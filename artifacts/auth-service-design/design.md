# FastAPI Auth Service - Technical Design

## Approach

This is a greenfield FastAPI authentication service built with modern Python async patterns and production-ready infrastructure. The design follows a layered architecture:

- **API Layer**: FastAPI routers handling HTTP requests/responses
- **Core Layer**: Business logic for authentication, JWT handling
- **Model Layer**: SQLAlchemy ORM models for data persistence
- **Utils Layer**: Cross-cutting concerns (password hashing, circuit breakers)
- **Infrastructure**: Logging, exception handling, configuration management

Key design principles:
- **Security First**: bcrypt password hashing, JWT with refresh tokens, input validation
- **Async by Default**: All database and external operations use async/await
- **Configuration-driven**: Environment variables with Pydantic validation
- **Observability**: Structured JSON logging with correlation IDs
- **Resilience**: Circuit breakers for external dependencies

## Detailed Changes

### Core Application Structure

**app/__init__.py**
- Empty initialization file for Python package structure

**app/config.py**
- Pydantic Settings class inheriting from BaseSettings
- Environment variables: DATABASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
- Validation for required settings with sensible defaults
- Support for both PostgreSQL (production) and SQLite (development)

**app/database.py**
- SQLAlchemy async engine configuration with connection pooling
- SessionLocal factory for dependency injection
- get_db() dependency function for FastAPI route injection
- Database initialization utilities

### Data Models

**app/models/user.py**
- SQLAlchemy User model with:
  - id: Primary key (Integer, autoincrement)
  - email: Unique string field with index
  - password_hash: String field for bcrypt hash
  - is_active: Boolean flag (default True)
  - created_at: UTC timestamp
  - updated_at: UTC timestamp with auto-update
- Proper table constraints and indexes for performance

**app/models/__init__.py**
- Import all models for Alembic discovery: `from .user import User`

### API Schemas

**app/schemas/auth.py**
- UserRegister: email validation, password complexity requirements
- UserLogin: email and password fields
- Token: access_token, refresh_token, token_type fields
- TokenData: username/email for JWT payload

**app/schemas/user.py**
- UserBase: Common user fields (email, is_active)
- UserCreate: Inherits UserBase, adds password validation
- UserResponse: Public user data (excludes password_hash)
- UserUpdate: Optional fields for profile updates

**app/schemas/__init__.py**
- Export all schema classes for easy imports

### Business Logic

**app/core/auth.py**
- create_access_token(): Generate JWT with expiration
- create_refresh_token(): Generate longer-lived refresh JWT
- verify_token(): Validate and decode JWT tokens
- get_current_user(): FastAPI dependency for protected routes
- authenticate_user(): Verify email/password combination

**app/core/exceptions.py**
- AuthenticationError: Invalid credentials
- AuthorizationError: Insufficient permissions
- ValidationError: Input validation failures
- DatabaseError: Database operation failures
- Custom exception handlers for FastAPI

**app/core/logging.py**
- Configure Python logging with JSON formatter
- Add correlation ID middleware for request tracking
- Structured logging with request context
- Log sanitization to avoid logging sensitive data

### Utilities

**app/utils/password.py**
- hash_password(): bcrypt password hashing with salt
- verify_password(): Password verification against hash
- Secure random salt generation

**app/utils/circuit_breaker.py**
- CircuitBreaker decorator for external service calls
- Configurable failure threshold and recovery timeout
- Integration with FastAPI dependency system

### API Endpoints

**app/api/auth.py**
- POST /auth/register: User registration with email/password
- POST /auth/login: User authentication returning JWT tokens
- POST /auth/refresh: Refresh access token using refresh token
- POST /auth/logout: Token invalidation (if using token blacklisting)
- All endpoints with proper OpenAPI documentation

**app/api/users.py**
- GET /users/me: Get current user profile
- PUT /users/me: Update user profile
- Protected endpoints requiring valid JWT

**app/api/__init__.py**
- Router aggregation for mounting to main FastAPI app

**app/main.py**
- FastAPI application factory with:
  - CORS middleware configuration
  - Exception handler registration
  - API router mounting
  - Request logging middleware
  - OpenAPI/Swagger documentation setup

## Interfaces

### Database Models

```python
class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True, nullable=False)
    password_hash: str = Column(String, nullable=False)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())
```

### API Endpoints

```python
# Authentication endpoints
POST /auth/register
  Request: {"email": "user@example.com", "password": "securepass123"}
  Response: {"id": 1, "email": "user@example.com", "is_active": true}

POST /auth/login
  Request: {"email": "user@example.com", "password": "securepass123"}
  Response: {"access_token": "jwt...", "refresh_token": "jwt...", "token_type": "bearer"}

POST /auth/refresh
  Request: {"refresh_token": "jwt..."}
  Response: {"access_token": "jwt...", "token_type": "bearer"}

# User endpoints
GET /users/me
  Headers: {"Authorization": "Bearer jwt..."}
  Response: {"id": 1, "email": "user@example.com", "is_active": true}
```

### Core Functions

```python
# Authentication utilities
async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None
async def create_access_token(data: dict, expires_delta: timedelta = None) -> str
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User

# Password utilities
def hash_password(password: str) -> str
def verify_password(plain_password: str, hashed_password: str) -> bool
```

## Trade-offs

### JWT vs Session-based Auth
**Chosen: JWT with refresh tokens**
- **Pro**: Stateless, scales horizontally, supports distributed systems
- **Con**: Larger token size, cannot easily revoke tokens
- **Mitigation**: Short access token expiry (15-30 min) with refresh mechanism

### SQLAlchemy Async vs Sync
**Chosen: Async SQLAlchemy**
- **Pro**: Better performance under load, non-blocking I/O
- **Con**: More complex code, learning curve
- **Justification**: FastAPI is async-native, better resource utilization

### Database Choice
**Chosen: PostgreSQL (production) / SQLite (development)**
- **Pro**: PostgreSQL provides ACID compliance, advanced features, production-ready
- **Con**: More complex setup than SQLite
- **Justification**: SQLite sufficient for development, PostgreSQL required for production scaling

### Exception Handling Strategy
**Chosen: Centralized exception handlers**
- **Pro**: Consistent error responses, better logging, cleaner code
- **Con**: Some indirection in error handling flow
- **Justification**: Better maintainability and user experience

## Open Questions

### For Implementation Agent:

1. **Rate Limiting**: Should we implement rate limiting middleware or rely on reverse proxy? Consider implementing basic rate limiting on auth endpoints.

2. **Token Storage**: Client-side token storage strategy - recommend localStorage with XSS protection or httpOnly cookies for refresh tokens.

3. **Password Requirements**: Specific password complexity rules beyond minimum length? Consider implementing configurable password policy.

4. **Email Verification**: Should user registration require email verification? This would add external email service dependency.

5. **User Roles/Permissions**: Current design supports basic authentication. Consider if role-based access control (RBAC) should be added to the User model.

6. **Database Migrations**: Alembic configuration and initial migration creation - should be automated during setup.

7. **Circuit Breaker Configuration**: Default failure thresholds and timeout values for external service calls.

8. **Logging Levels**: Default log levels for different environments (DEBUG in development, INFO in production).

9. **CORS Configuration**: Specific allowed origins and methods - should be environment-configurable.

10. **Health Check Endpoints**: Consider adding `/health` and `/readiness` endpoints for container orchestration.

### Security Considerations:

- JWT secret key rotation strategy
- Password hash cost factor (bcrypt rounds) balancing security vs performance
- Request size limits to prevent DoS attacks
- SQL injection prevention through ORM usage verification
- Sensitive data sanitization in logs and error messages