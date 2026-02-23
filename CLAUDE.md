# FastAPI Authentication Service

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: SQLite (development), PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT tokens with passlib for password hashing
- **Documentation**: FastAPI automatic OpenAPI/Swagger docs
- **Testing**: pytest with pytest-asyncio for async tests
- **Logging**: Python standard logging with structured output
- **Validation**: Pydantic models for request/response validation
- **Circuit Breaker**: circuitbreaker library for resilience

## Project Structure
```
auth-serve/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection and session management
│   ├── models/            # SQLAlchemy database models
│   │   ├── __init__.py
│   │   └── user.py        # User model
│   ├── schemas/           # Pydantic models for API
│   │   ├── __init__.py
│   │   ├── user.py        # User request/response models
│   │   └── auth.py        # Authentication models
│   ├── api/               # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py        # Authentication endpoints
│   │   └── users.py       # User management endpoints
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py    # Password hashing, JWT tokens
│   │   ├── exceptions.py  # Custom exceptions
│   │   └── circuit_breaker.py # Circuit breaker implementation
│   └── utils/             # Utility functions
│       ├── __init__.py
│       └── logging.py     # Logging configuration
├── tests/                 # Test files
│   ├── __init__.py
│   ├── conftest.py       # Test configuration and fixtures
│   ├── test_auth.py      # Authentication endpoint tests
│   └── test_users.py     # User endpoint tests
├── requirements.txt       # Dependencies
├── pyproject.toml        # Project configuration
└── README.md             # Project documentation
```

## Coding Conventions
- **Naming Style**: snake_case for variables, functions, and files; PascalCase for classes
- **Import Ordering**: Standard library, third-party packages, local imports (separated by blank lines)
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Google-style docstrings for all public functions and classes
- **Line Length**: Maximum 88 characters (Black formatter default)
- **Async/Await**: Use async/await for all database operations and external calls
- **Error Handling**: Use FastAPI HTTPException for API errors, custom exceptions for business logic

## Commands
- **Install Dependencies**: `pip install -r requirements.txt`
- **Run Development Server**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run Tests**: `pytest -v`
- **Run Tests with Coverage**: `pytest --cov=app --cov-report=html`
- **Format Code**: `black app/ tests/`
- **Lint Code**: `flake8 app/ tests/`
- **Type Check**: `mypy app/`

## Key Patterns
- **Dependency Injection**: Use FastAPI's Depends() for database sessions and authentication
- **Repository Pattern**: Separate data access logic into repository classes
- **Response Models**: Always use Pydantic models for API responses to ensure data validation
- **Exception Handling**: Centralized exception handler middleware for consistent error responses
- **Configuration**: Use environment variables with Pydantic Settings for configuration management
- **Database Sessions**: Use async context managers for database transactions
- **JWT Authentication**: Bearer token authentication with automatic user context injection
- **Circuit Breaker**: Wrap external service calls with circuit breaker pattern for resilience