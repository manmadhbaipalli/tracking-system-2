# Auth Serve Technical Design

## Approach

This design implements a FastAPI-based authentication service following a layered architecture with clear separation of concerns:

1. **API Layer**: FastAPI endpoints with Pydantic schema validation
2. **Business Logic Layer**: Core services for authentication, security, and utilities
3. **Data Layer**: SQLAlchemy models with Alembic migrations
4. **Infrastructure Layer**: Logging, exception handling, and circuit breaker patterns

The implementation prioritizes security, scalability, and maintainability with async/await patterns throughout.

## Detailed Changes

### Core Application Structure

**app/main.py**
- Create FastAPI application instance
- Configure CORS middleware for cross-origin requests
- Register global exception handlers from `app.core.exceptions`
- Setup centralized logging from `app.core.logging`
- Include API v1 router with `/api/v1` prefix
- Add startup event handlers for database initialization
- Enable automatic OpenAPI/Swagger documentation

**app/config.py**
- Define `Settings` class using `pydantic_settings.BaseSettings`
- Environment variables: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- Optional variables: `DEBUG`, `LOG_LEVEL`, `CORS_ORIGINS`
- Provide development defaults for local testing

**app/database.py**
- Create async SQLAlchemy engine with connection pooling
- Define `AsyncSessionLocal` factory for database sessions
- Implement `get_db()` dependency for FastAPI dependency injection
- Setup declarative base for SQLAlchemy models
- Configure async session management with proper cleanup

### Data Models and Schemas

**app/models/user.py**
- Define `User` SQLAlchemy model with:
  - `id`: Primary key (UUID or Integer)
  - `email`: Unique, indexed, non-null string
  - `username`: Unique, indexed, non-null string
  - `hashed_password`: Non-null string (never expose in responses)
  - `is_active`: Boolean flag for account status
  - `created_at`, `updated_at`: Timestamp fields
- Add table constraints for email and username uniqueness
- Include proper indexing for query performance

**app/schemas/user.py**
- `UserCreate`: Email, username, password with validation rules
- `UserResponse`: Public user data (exclude hashed_password)
- `UserUpdate`: Optional fields for profile updates
- Email validation using Pydantic's `EmailStr`
- Password strength validation (minimum length, complexity)

**app/schemas/auth.py**
- `LoginRequest`: Username/email and password fields
- `TokenResponse`: Access token, token type, and expiration
- `RegisterRequest`: User registration data with confirmation fields

### Authentication and Security

**app/core/security.py**
- `hash_password()`: Bcrypt password hashing with proper salt rounds
- `verify_password()`: Password verification against hash
- `create_access_token()`: JWT token generation with expiration
- `decode_access_token()`: JWT token validation and parsing
- `get_current_user()`: FastAPI dependency for authenticated routes
- Secure random secret key generation utilities

**app/api/v1/auth.py**
- `POST /register`: User registration with duplicate checking
  - Validate input data using `RegisterRequest` schema
  - Check for existing email/username conflicts
  - Hash password and create user record
  - Return success response (no auto-login for security)
- `POST /login`: User authentication with JWT token generation
  - Validate credentials using `LoginRequest` schema
  - Verify password against stored hash
  - Generate and return JWT access token
  - Handle invalid credentials with proper error responses

**app/api/v1/users.py**
- `GET /users/me`: Get current user profile
  - Require valid JWT token via `get_current_user` dependency
  - Return user data using `UserResponse` schema
  - Handle authentication errors appropriately

### Infrastructure Components

**app/core/logging.py**
- Configure structured JSON logging with correlation IDs
- Set up different log levels for development vs production
- Include request/response logging middleware
- Add contextual logging utilities for tracing requests
- Configure log rotation and output destinations

**app/core/exceptions.py**
- Define custom exception classes:
  - `AuthenticationException`: 401 Unauthorized errors
  - `AuthorizationException`: 403 Forbidden errors
  - `ValidationException`: 422 Unprocessable Entity errors
  - `NotFoundException`: 404 Not Found errors
- Implement global exception handlers for FastAPI
- Ensure sensitive information is not leaked in error responses
- Provide consistent error response format

**app/core/circuit_breaker.py**
- Implement circuit breaker decorator using `circuitbreaker` library
- Configure failure thresholds and recovery timeouts
- Add monitoring and logging for circuit breaker state changes
- Provide utilities for external service call protection
- Include health check endpoints integration

### Database Migrations

**alembic.ini**
- Configure Alembic with async SQLAlchemy URL
- Set migration directory and script templates
- Configure logging and output formatting

**alembic/env.py**
- Setup async migration environment
- Import application models for autogeneration
- Configure database connection from application settings
- Handle both online and offline migration modes

**alembic/versions/001_create_users.py**
- Create initial migration for users table
- Include all user model fields with proper types
- Add unique constraints and indexes
- Set up proper foreign key relationships if needed

### Configuration Files

**requirements.txt**
```
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
sqlalchemy[asyncio]>=2.0.0
alembic>=1.10.0
pydantic-settings>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
circuitbreaker>=1.4.0
```

**requirements-dev.txt**
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
```

**.env.example**
```
DATABASE_URL=sqlite+aiosqlite:///./test.db
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

**pytest.ini**
```ini
[tool:pytest]
testpaths = tests
asyncio_mode = auto
addopts = --cov=app --cov-report=term-missing
```

## Interfaces

### API Endpoints

**Authentication Endpoints**
- `POST /api/v1/auth/register`
  - Input: `RegisterRequest` (email, username, password, password_confirm)
  - Output: `{"message": "User created successfully"}`
  - Status Codes: 201 (Created), 400 (Bad Request), 409 (Conflict)

- `POST /api/v1/auth/login`
  - Input: `LoginRequest` (username, password)
  - Output: `TokenResponse` (access_token, token_type, expires_in)
  - Status Codes: 200 (OK), 401 (Unauthorized), 422 (Validation Error)

**User Endpoints**
- `GET /api/v1/users/me`
  - Headers: `Authorization: Bearer <jwt_token>`
  - Output: `UserResponse` (id, email, username, is_active, created_at)
  - Status Codes: 200 (OK), 401 (Unauthorized)

### Internal Interfaces

**Security Functions**
```python
async def hash_password(password: str) -> str
async def verify_password(plain_password: str, hashed_password: str) -> bool
def create_access_token(data: dict, expires_delta: timedelta = None) -> str
async def decode_access_token(token: str) -> dict
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User
```

**Database Dependencies**
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]
```

## Trade-offs

### Security vs Usability
- **Chosen**: Secure defaults with bcrypt and JWT expiration
- **Alternative**: Longer token expiration for better UX
- **Rationale**: Security is paramount for authentication service

### Database Choice
- **Chosen**: SQLite for development, PostgreSQL for production
- **Alternative**: Single database for simplicity
- **Rationale**: SQLite enables easy local development, PostgreSQL provides production scalability

### Password Requirements
- **Chosen**: Basic length validation with strong hashing
- **Alternative**: Complex password rules
- **Rationale**: Avoid user friction while maintaining security through proper hashing

### Error Handling
- **Chosen**: Detailed error responses for development, generic for production
- **Alternative**: Always generic error messages
- **Rationale**: Better developer experience while maintaining production security

### Circuit Breaker Implementation
- **Chosen**: Library-based circuit breaker with configuration
- **Alternative**: Custom implementation
- **Rationale**: Proven library reduces complexity and provides monitoring

## Open Questions

### Implementation Decisions

1. **User Identification**: Should login accept email, username, or both?
   - Recommendation: Support both email and username for login flexibility

2. **Token Storage**: Should we implement refresh tokens or rely on short-lived access tokens?
   - Recommendation: Start with access tokens only, add refresh tokens if needed

3. **Rate Limiting**: Should we implement rate limiting at the application level?
   - Recommendation: Document but leave for deployment-level implementation (nginx, load balancer)

4. **User Activation**: Should new users require email verification?
   - Recommendation: Start with immediate activation, add email verification as enhancement

5. **Password Reset**: Should password reset functionality be included in initial implementation?
   - Recommendation: Document as future enhancement, focus on core authentication first

6. **User Roles**: Should we implement role-based access control?
   - Recommendation: Add basic `is_active` flag, implement roles as future enhancement

7. **Session Management**: Should we track active sessions?
   - Recommendation: Stateless JWT approach initially, add session tracking if needed

### Configuration Questions

1. **Default JWT Expiration**: What should be the default token expiration time?
   - Recommendation: 30 minutes for access tokens

2. **Database URL Format**: Should we support both sync and async database URLs?
   - Recommendation: Async URLs only for consistency

3. **CORS Configuration**: What should be the default CORS policy?
   - Recommendation: Restrictive by default, configurable via environment variables