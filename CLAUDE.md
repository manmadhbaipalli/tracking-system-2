# Auth Service Project Standards

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI (modern async web framework)
- **Database**: PostgreSQL (relational database for user data)
- **ORM**: SQLAlchemy (database abstraction layer)
- **Testing**: pytest (test framework with fixtures)
- **Package Manager**: pip / poetry
- **Async Support**: asyncio, httpx (for async HTTP calls)
- **Security**: PyJWT (JWT tokens), passlib + bcrypt (password hashing), python-multipart (form data)
- **API Documentation**: Swagger/OpenAPI (built into FastAPI)
- **Logging**: Python logging module (standard library)
- **Validation**: Pydantic (data validation and serialization)
- **Environment Configuration**: python-dotenv (environment variables)

## Project Structure

The project will follow this structure:

```
auth-service-agent-1/
├── CLAUDE.md                          # This file - project standards
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
├── .env.example                       # Example environment variables
├── .gitignore                         # Git ignore rules
├── app/                               # Main application package
│   ├── __init__.py
│   ├── main.py                        # FastAPI app initialization
│   ├── config.py                      # Configuration and settings
│   ├── models/                        # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── user.py                    # User model
│   ├── schemas/                       # Pydantic schemas for request/response
│   │   ├── __init__.py
│   │   └── user.py                    # User schemas (LoginRequest, RegisterRequest, etc.)
│   ├── database/                      # Database setup and session management
│   │   ├── __init__.py
│   │   └── connection.py              # Database connection and session factory
│   ├── handlers/                      # Exception and error handlers
│   │   ├── __init__.py
│   │   └── exceptions.py              # Custom exceptions and handlers
│   ├── services/                      # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py            # Authentication logic
│   │   └── circuit_breaker.py         # Circuit breaker pattern
│   ├── routers/                       # API route handlers
│   │   ├── __init__.py
│   │   └── auth.py                    # /login, /register endpoints
│   ├── middleware/                    # Custom middleware
│   │   ├── __init__.py
│   │   └── logging.py                 # Logging middleware
│   └── utils/                         # Utility functions
│       ├── __init__.py
│       └── security.py                # JWT, password hashing utilities
├── migrations/                        # Alembic database migrations
│   ├── versions/
│   ├── env.py
│   ├── script.py.mako
│   └── alembic.ini
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures and configuration
│   ├── test_auth.py                   # Auth endpoint tests
│   ├── test_models.py                 # Model tests
│   ├── test_services.py               # Service layer tests
│   └── test_circuit_breaker.py        # Circuit breaker tests
├── artifacts/                         # Analysis and design documents
│   └── auth-service-analysis/
│       ├── analysis.md                # Detailed analysis document
│       ├── database-schema.sql        # SQL schema
│       └── diagrams/                  # PlantUML diagrams
│           ├── sequence-diagram.puml
│           └── flow-diagram.puml
├── docker/                            # Docker configuration (optional)
│   ├── Dockerfile
│   └── docker-compose.yml
└── scripts/                           # Utility scripts
    └── setup_db.py                    # Database initialization script
```

## Coding Conventions

### Python Style
- **PEP 8 Compliance**: Follow PEP 8 with line length of 100 characters
- **Formatting**: Use Black for code formatting
- **Linting**: Use Flake8 or Ruff for linting
- **Type Hints**: Always use type hints for function signatures and class variables
- **Imports**: Organize imports in three groups: stdlib, third-party, local (sorted alphabetically within groups)
  ```python
  # stdlib
  import os
  from typing import Optional

  # third-party
  from fastapi import FastAPI, HTTPException
  from sqlalchemy import Column, String

  # local
  from app.config import settings
  from app.models.user import User
  ```

### Naming Conventions
- **Classes**: PascalCase (e.g., `UserService`, `AuthException`)
- **Functions/Methods**: snake_case (e.g., `validate_password`, `create_user`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_LOGIN_ATTEMPTS`, `TOKEN_EXPIRY`)
- **Private Methods**: Leading underscore (e.g., `_hash_password`)
- **Database Tables**: snake_case (e.g., `users`, `refresh_tokens`)

### Code Organization
- **One responsibility per class/module**: Follow Single Responsibility Principle
- **Async functions**: Use `async def` for I/O operations, prefix async context managers with `async with`
- **Exception handling**: Catch specific exceptions, not `Exception`
- **Logging**: Use module-level logger: `logger = logging.getLogger(__name__)`
- **Docstrings**: Use Google-style docstrings for public functions/classes:
  ```python
  def authenticate_user(username: str, password: str) -> Optional[User]:
      """Authenticate a user by username and password.

      Args:
          username: The user's username.
          password: The user's plaintext password.

      Returns:
          The authenticated User object or None if authentication fails.

      Raises:
          AuthenticationError: If authentication fails.
      """
  ```

### FastAPI Patterns
- **Dependency Injection**: Use FastAPI's `Depends()` for injecting dependencies
- **Request/Response Models**: Define Pydantic models for all endpoints
- **Status Codes**: Use appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 500)
- **Error Responses**: Use `HTTPException` with consistent error format:
  ```python
  from fastapi import HTTPException
  raise HTTPException(status_code=401, detail="Invalid credentials")
  ```

### Database Patterns
- **SQLAlchemy Models**: Define ORM models in `models/` directory
- **Session Management**: Use context managers for database sessions
- **Migrations**: Use Alembic for schema migrations
- **Transactions**: Wrap operations in database transactions

### Testing Patterns
- **Test Organization**: Group tests by module (test_auth.py, test_services.py)
- **Fixtures**: Use pytest fixtures in `conftest.py` for setup/teardown
- **Mocking**: Use `unittest.mock` or `pytest-mock` for external dependencies
- **Test Names**: Use descriptive names: `test_register_user_success`, `test_login_invalid_password`
- **Coverage**: Aim for >80% code coverage

## Commands

### Setup & Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python scripts/setup_db.py
```

### Running the Application
```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_login"
```

### Database
```bash
# Create migrations
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality
```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/

# All checks together
black --check app/ tests/ && flake8 app/ tests/ && mypy app/
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Key Patterns

### 1. Service Layer Pattern
Business logic is separated from route handlers into service classes:
```python
# In app/services/auth_service.py
class AuthService:
    async def register_user(self, username: str, email: str, password: str) -> User:
        # Implementation

    async def authenticate_user(self, username: str, password: str) -> User:
        # Implementation
```

### 2. Dependency Injection
FastAPI's dependency system is used for injecting services and database sessions:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# In route handler
@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.authenticate_user(...)
```

### 3. Circuit Breaker Pattern
For external service calls, implement circuit breaker to handle failures:
```python
class CircuitBreaker:
    async def call(self, func, *args, **kwargs):
        # Check state and call function with fallback
```

### 4. Custom Exception Handling
Centralized exception handlers for consistent error responses:
```python
@app.exception_handler(AuthenticationError)
async def auth_error_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)}
    )
```

### 5. Structured Logging
All modules use structured logging with correlation IDs for tracing:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("User registration", extra={"user_id": user.id, "request_id": request_id})
```

## Development Workflow

1. **Create a new branch** for features: `git checkout -b feature/feature-name`
2. **Write tests first** (TDD approach when possible)
3. **Implement feature** following coding conventions
4. **Run tests and linters** before committing
5. **Commit with clear messages**: `git commit -m "feat: add user registration endpoint"`
6. **Create pull request** for code review

## Environment Variables

Create a `.env` file based on `.env.example`:
```
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/auth_db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Security
MAX_LOGIN_ATTEMPTS=5
LOGIN_ATTEMPT_TIMEOUT=900
```

## Notes for Agents

- This is a greenfield FastAPI project for building an authentication service
- All new code should be async-first (using `async`/`await`)
- Use SQLAlchemy ORM with async support (`asyncpg` driver for PostgreSQL)
- Implement comprehensive tests for all business logic
- Use Pydantic for request/response validation
- Centralize all error handling and logging
- Document all endpoints with OpenAPI decorators for Swagger
