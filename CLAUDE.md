# Auth Serve Project - Coding Standards

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0+ with Alembic for migrations
- **Authentication**: JWT tokens with passlib for password hashing
- **Testing**: pytest with pytest-asyncio
- **Documentation**: Swagger/OpenAPI (built-in FastAPI)
- **Logging**: Python logging with structured JSON format
- **Circuit Breaker**: circuitbreaker library
- **Environment**: pydantic-settings for configuration

## Project Structure
```
auth-serve/
├── app/                    # Main application code
│   ├── __init__.py
│   ├── main.py            # FastAPI app instance and startup
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection and session management
│   ├── models/            # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py        # User model
│   ├── schemas/           # Pydantic schemas for request/response
│   │   ├── __init__.py
│   │   ├── user.py        # User schemas
│   │   └── auth.py        # Auth schemas
│   ├── api/               # API endpoints
│   │   ├── __init__.py
│   │   ├── v1/            # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── auth.py    # Authentication endpoints
│   │   │   └── users.py   # User management endpoints
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py    # JWT and password handling
│   │   ├── logging.py     # Centralized logging setup
│   │   ├── exceptions.py  # Custom exceptions and handlers
│   │   └── circuit_breaker.py # Circuit breaker utilities
│   └── utils/             # Utility functions
│       ├── __init__.py
│       └── helpers.py     # Common helper functions
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py        # pytest configuration and fixtures
│   ├── test_auth.py       # Authentication endpoint tests
│   ├── test_users.py      # User endpoint tests
│   └── test_models.py     # Model tests
├── alembic/               # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── alembic.ini           # Alembic configuration
├── pytest.ini           # pytest configuration
├── .env.example          # Environment variables template
└── README.md             # Project documentation
```

## Coding Conventions
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Import ordering**: Standard library, third-party, local imports (use isort)
- **Formatting**: Black formatter with 88-character line length
- **Type hints**: Required for all public functions and methods
- **Docstrings**: Google-style for all public functions/classes
- **Error handling**: Use custom exceptions with proper HTTP status codes
- **Async**: Use async/await for all I/O operations

## Commands
- **Start app**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run tests**: `pytest -v --cov=app`
- **Lint code**: `black app tests && isort app tests && flake8 app tests`
- **Database migrations**:
  - Create: `alembic revision --autogenerate -m "description"`
  - Apply: `alembic upgrade head`
- **Install deps**: `pip install -r requirements.txt` (prod) / `pip install -r requirements-dev.txt` (dev)

## Key Patterns
- **Dependency injection**: Use FastAPI's Depends() for database sessions, auth, etc.
- **Repository pattern**: Separate data access from business logic
- **Schema validation**: Pydantic models for all request/response data
- **Error handling**: Centralized exception handlers with proper HTTP status codes
- **Configuration**: Environment-based config using pydantic-settings
- **Logging**: Structured JSON logs with correlation IDs
- **Testing**: Factory pattern for test data, separate test database