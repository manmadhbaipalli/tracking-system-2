# Project Standards & Conventions

## Tech Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI (async web framework)
- **Database**: SQLAlchemy with SQLite/PostgreSQL (to be determined during implementation)
- **Authentication**: JWT (JSON Web Tokens)
- **Key Libraries**:
  - `fastapi`: Web framework
  - `sqlalchemy`: ORM
  - `pydantic`: Data validation
  - `python-jose`: JWT implementation
  - `passlib`: Password hashing
  - `pytest`: Testing framework
  - `pytest-asyncio`: Async test support
  - `pydentic-settings`: Configuration management
  - `structlog` or `python-logging`: Structured logging
  - `tenacity`: Circuit breaker/retry patterns

## Project Structure
```
auth-agent-1/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── dependencies.py         # Dependency injection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # SQLAlchemy User model
│   │   └── schemas.py         # Pydantic schemas for API
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # Login/registration endpoints
│   │   └── health.py          # Health check endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Authentication business logic
│   │   └── user_service.py    # User management
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py         # Request/response logging
│   │   └── exception.py       # Global exception handler
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── jwt.py             # JWT utilities
│   │   ├── password.py        # Password hashing/verification
│   │   ├── circuit_breaker.py # Circuit breaker implementation
│   │   └── logger.py          # Centralized logging setup
│   └── database.py            # Database connection management
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_auth_service.py
│   │   └── test_user_service.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_auth_routes.py
│   │   └── test_user_routes.py
│   └── fixtures/
│       ├── __init__.py
│       └── database.py
├── requirements.txt
├── .env.example
├── pytest.ini
├── CLAUDE.md
└── artifacts/
    └── auth-analysis/
        └── analysis.md
```

## Coding Conventions

### Python Style
- Follow PEP 8 conventions
- Use type hints for all function parameters and returns
- Use `snake_case` for variables, functions, and modules
- Use `PascalCase` for classes
- Imports: stdlib → third-party → local (one blank line between sections)
- Line length: 100 characters (for readability)

### FastAPI Patterns
- Use dependency injection via `Depends()` for authentication, logging, DB session
- Use path parameters for resource IDs, query parameters for filtering
- Return Pydantic models for all endpoints
- Use HTTP status codes appropriately (200, 201, 400, 401, 403, 404, 500)
- Include proper error responses with detail messages

### Database Patterns
- Use SQLAlchemy declarative base for models
- Use Pydantic schemas separate from ORM models
- Always use async context managers for DB sessions
- Implement repository pattern for data access

### Testing Patterns
- Pytest with pytest-asyncio for async support
- Use fixtures for common setup (DB, auth tokens, users)
- Separate unit tests from integration tests
- Use mocking for external dependencies
- Aim for 80%+ code coverage

### Logging Patterns
- Use structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include request ID in all log entries for traceability
- Log sensitive data redacted (never log passwords, tokens)

## Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_auth_service.py -v

# Lint code
flake8 app/ tests/

# Format code
black app/ tests/

# Type checking
mypy app/
```

### Database
```bash
# Create database schema
alembic upgrade head

# Generate migration
alembic revision --autogenerate -m "Description"
```

## Key Patterns

### Authentication Flow
- User registration: Create user, hash password, store in DB
- Login: Validate credentials, generate JWT token, return to client
- Protected routes: Validate JWT, extract user info from token, inject into route
- Token refresh: Implement refresh token mechanism for long-lived sessions

### Error Handling
- Custom exception hierarchy: `BaseException` → `AuthException`, `ValidationException`, etc.
- Global exception handler middleware that catches all exceptions
- Return consistent error response format: `{"detail": "error message", "error_code": "CODE"}`

### Circuit Breaker
- Implement for external service calls (if applicable)
- States: Closed (normal), Open (fail fast), Half-Open (testing recovery)
- Track failures by service/endpoint
- Use exponential backoff for retries

### Dependency Injection
- `get_db()`: Provide DB session to routes
- `get_current_user()`: Validate JWT and return current user
- `get_logger()`: Provide configured logger to routes

## Configuration
- Use environment variables via `.env` file and `pydantic-settings`
- Separate configs: development, testing, production
- Never commit `.env` files with secrets
- Use `.env.example` template showing required variables

## Security Considerations
- Always hash passwords (bcrypt via passlib)
- Use HTTPS in production (enforced via settings)
- CORS configuration to restrict origin
- Implement rate limiting on auth endpoints
- JWT expiration: short-lived access tokens (15-30 min), long-lived refresh tokens (7 days)
- Add request ID middleware for audit trails
- Implement proper exception handling to avoid information disclosure
