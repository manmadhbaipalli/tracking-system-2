# Project Standards

## Tech Stack
- **Language**: Python 3.8+
- **Framework**: FastAPI
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Authentication**: JWT tokens with passlib for password hashing
- **Testing**: pytest, httpx for async testing
- **Documentation**: Auto-generated OpenAPI/Swagger docs via FastAPI
- **Logging**: Python logging module with structured logging
- **Dependency Management**: pip with requirements.txt

## Project Structure
```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance and startup
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── crud.py              # Database operations
│   ├── auth.py              # Authentication utilities (JWT, password hashing)
│   ├── database.py          # Database connection and session management
│   ├── exceptions.py        # Custom exception classes and handlers
│   ├── logging_config.py    # Centralized logging configuration
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # Login/registration endpoints
│       └── users.py         # User management endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test configuration and fixtures
│   ├── test_auth.py         # Authentication endpoint tests
│   └── test_users.py        # User endpoint tests
├── requirements.txt         # Project dependencies
└── README.md               # Project documentation
```

## Coding Conventions
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Import ordering**: Standard library, third-party, local imports (separated by blank lines)
- **Line length**: 88 characters (Black formatter standard)
- **Docstrings**: Google-style docstrings for functions and classes
- **Type hints**: Use throughout codebase for better IDE support and maintainability
- **Async/await**: Use async endpoints for I/O operations (database, external APIs)

## Commands
- **Install dependencies**: `pip install -r requirements.txt`
- **Run app**: `uvicorn app.main:app --reload`
- **Run tests**: `pytest -v`
- **Run specific test**: `pytest tests/test_auth.py -v`
- **Check test coverage**: `pytest --cov=app --cov-report=html`

## Key Patterns
- **Dependency Injection**: Use FastAPI's dependency injection for database sessions, authentication
- **Repository Pattern**: CRUD operations separated into crud.py module
- **Schema Validation**: Separate Pydantic schemas for request/response validation
- **Exception Handling**: Custom exception classes with centralized error handlers
- **Configuration**: Use environment variables for configuration (database URLs, JWT secrets)
- **Logging**: Structured logging with correlation IDs for request tracing