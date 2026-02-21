# Auth Service App - FastAPI Project

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **Database**: SQLite (development), PostgreSQL (production ready)
- **ORM**: SQLAlchemy 2.0+ with Alembic migrations
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: bcrypt via passlib
- **Validation**: Pydantic v2
- **Testing**: pytest with pytest-asyncio
- **Documentation**: Auto-generated OpenAPI/Swagger via FastAPI
- **Logging**: Python standard logging with structured JSON output
- **Circuit Breaker**: circuitbreaker library

## Project Structure
```
/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── core/                # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py        # Settings and configuration
│   │   ├── security.py      # JWT and password utilities
│   │   ├── logging.py       # Centralized logging setup
│   │   └── exceptions.py    # Custom exceptions and handlers
│   ├── api/                 # API route definitions
│   │   ├── __init__.py
│   │   ├── deps.py          # Dependencies (DB session, auth, etc.)
│   │   └── v1/              # API version 1
│   │       ├── __init__.py
│   │       ├── auth.py      # Authentication endpoints
│   │       └── users.py     # User management endpoints
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py          # User model
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py          # User schemas
│   │   └── token.py         # Token schemas
│   ├── crud/                # CRUD operations
│   │   ├── __init__.py
│   │   └── user.py          # User CRUD operations
│   └── db/                  # Database related
│       ├── __init__.py
│       ├── base.py          # Base class imports
│       ├── session.py       # Database session handling
│       └── init_db.py       # Database initialization
├── alembic/                 # Database migrations
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration and fixtures
│   ├── test_main.py         # Main app tests
│   ├── api/                 # API endpoint tests
│   │   ├── __init__.py
│   │   └── test_auth.py     # Authentication tests
│   └── crud/                # CRUD tests
│       ├── __init__.py
│       └── test_user.py     # User CRUD tests
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── pyproject.toml           # Project configuration
├── alembic.ini             # Alembic configuration
├── .env.example            # Environment variables template
└── README.md               # Project documentation
```

## Coding Conventions
- **Style**: Follow PEP 8 with Black formatter (line length 88)
- **Import Ordering**: isort with profile "black"
- **Type Hints**: Use throughout codebase, prefer modern syntax (list[str] over List[str])
- **Naming**:
  - snake_case for variables, functions, modules
  - PascalCase for classes
  - UPPER_CASE for constants
- **Async**: Use async/await for all I/O operations (database, external calls)
- **Error Handling**: Raise HTTPException for API errors, custom exceptions for business logic

## Commands
- **Install Dependencies**: `pip install -r requirements-dev.txt`
- **Run App**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run Tests**: `pytest -v`
- **Run Tests with Coverage**: `pytest --cov=app --cov-report=html`
- **Format Code**: `black . && isort .`
- **Type Check**: `mypy app/`
- **Database Migration**: `alembic revision --autogenerate -m "description"`
- **Apply Migrations**: `alembic upgrade head`

## Key Patterns
- **Dependency Injection**: Use FastAPI's dependency injection for database sessions, authentication
- **Repository Pattern**: CRUD operations separated from API logic
- **Schema Validation**: Separate Pydantic models for request/response validation
- **Configuration**: Use Pydantic BaseSettings for type-safe configuration
- **Error Handling**: Global exception handlers with structured error responses
- **Logging**: Structured JSON logging with correlation IDs for request tracing
- **Security**: JWT tokens with refresh mechanism, password hashing with salt
- **Circuit Breaker**: Applied to external service calls and database operations that may fail
- **Testing**: Separate test database, factory pattern for test data creation