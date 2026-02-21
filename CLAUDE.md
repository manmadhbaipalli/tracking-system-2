# CLAUDE.md - Project Standards

## Tech Stack
- **Language**: Python 3.9+
- **Framework**: FastAPI (modern async web framework)
- **Database**: SQLite (for dev/test) or PostgreSQL (recommended for production)
- **Authentication**: JWT tokens with password hashing (bcrypt)
- **API Documentation**: Swagger/OpenAPI (built-in with FastAPI)
- **Testing**: pytest + pytest-asyncio
- **Logging**: Python logging module with structured logging
- **Circuit Breaker**: pybreaker library for resilience

## Project Structure
```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py        # Registration & login endpoints
│   │   ├── schemas.py       # Pydantic models for auth
│   │   └── utils.py         # Password hashing, JWT token handling
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # SQLAlchemy User model
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py            # Database session management
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py       # Centralized request/response logging
│   │   └── exception.py     # Global exception handling
│   └── utils/
│       ├── __init__.py
│       └── circuit_breaker.py  # Circuit breaker for external calls
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_auth.py         # Auth endpoint tests
│   ├── test_integration.py  # Integration tests
│   └── test_circuit_breaker.py  # Circuit breaker tests
├── requirements.txt         # Python dependencies
├── pytest.ini              # Pytest configuration
└── README.md               # Project documentation
```

## Coding Conventions
- **Style**: Follow PEP 8, use Black for formatting
- **Imports**: Group standard library, third-party, local (in that order)
- **Naming**:
  - Classes: PascalCase
  - Functions/variables: snake_case
  - Constants: UPPER_CASE
- **Type Hints**: Required for function signatures
- **Async**: Use `async def` for all route handlers and database operations
- **Error Handling**: Use custom exception classes with meaningful messages

## Commands
- **Install dependencies**: `pip install -r requirements.txt`
- **Run app**: `uvicorn app.main:app --reload`
- **Run tests**: `pytest -v`
- **Run tests with coverage**: `pytest --cov=app tests/`
- **Format code**: `black app/ tests/`
- **Lint**: `flake8 app/ tests/`

## Key Patterns
1. **Dependency Injection**: FastAPI's `Depends()` for database sessions and authentication
2. **Middleware**: Use ASGI middleware for logging and exception handling
3. **Pydantic Models**: For request/response validation and serialization
4. **SQLAlchemy ORM**: For database operations
5. **JWT Tokens**: Stateless authentication using tokens
6. **Circuit Breaker**: Wrap external API calls to prevent cascading failures
7. **Logging**: Structured logging with request IDs for traceability
