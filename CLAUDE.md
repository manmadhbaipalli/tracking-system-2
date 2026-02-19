# FastAPI Auth Service - Project Standards

## Tech Stack
- **Language**: Python 3.9+
- **Framework**: FastAPI (async web framework)
- **Database**: SQLAlchemy ORM (supports PostgreSQL, SQLite, MySQL)
- **Authentication**: JWT (JSON Web Tokens) with password hashing via bcrypt
- **API Documentation**: Swagger/OpenAPI (built-in with FastAPI)
- **Testing**: pytest with pytest-asyncio for async test support
- **Logging**: Python's `logging` module with structured logging support
- **Circuit Breaker**: pybreaker library
- **Validation**: Pydantic for request/response validation
- **Task Queue** (optional): Celery or background tasks for async operations

## Project Structure
```
auth-serve-agent-1/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py             # User database model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py             # Pydantic models for request/response
│   ├── routes/
│   │   ├── __init__.py
│   │   └── auth.py             # Login, registration endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py     # Business logic for authentication
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # Centralized logging configuration
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── circuit_breaker.py  # Circuit breaker wrapper
│   │   └── security.py         # JWT, hashing utilities
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── error_handler.py    # Global exception handler
│   │   └── logging_middleware.py
│   └── database.py             # SQLAlchemy session management
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_auth_routes.py     # Route tests
│   └── test_auth_service.py    # Service logic tests
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── docker-compose.yml          # Optional: Database setup
└── README.md
```

## Coding Conventions
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPERCASE_WITH_UNDERSCORES`
  - Private members: `_leading_underscore`
- **Import Ordering**: stdlib → third-party → local
- **Type Hints**: Use throughout for clarity (PEP 484)
- **Docstrings**: Google-style docstrings for functions and classes
- **Max Line Length**: 100 characters
- **Formatting**: Black formatter compatible
- **Linting**: Flake8 compatible

## Commands
- **Run Application**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run Tests**: `pytest tests/ -v --cov=app`
- **Run Async Tests**: `pytest tests/ -v --cov=app -p no:warnings`
- **Lint**: `flake8 app tests` or `black --check app tests`
- **Format**: `black app tests`
- **Database Migrations** (if using Alembic): `alembic upgrade head`

## Key Patterns
1. **Dependency Injection**: FastAPI's `Depends()` for injecting services and database sessions
2. **Service Layer**: Business logic separated from route handlers
3. **Pydantic Models**: Strict validation at API boundaries
4. **Exception Handling**: Custom exceptions with HTTP response mapping
5. **Circuit Breaker Pattern**: For external service calls with graceful degradation
6. **Middleware**: For cross-cutting concerns (logging, error handling)
7. **Context Managers**: For database session management
8. **Async/Await**: All I/O operations should be async
