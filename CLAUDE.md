# Project Standards

## Tech Stack
- **Language**: Python 3.9+
- **Framework**: FastAPI
- **Database**: SQLAlchemy ORM with SQLite (dev) / PostgreSQL (prod)
- **Testing**: pytest
- **Authentication**: JWT tokens (PyJWT)
- **Circuit Breaker**: pybreaker
- **Logging**: Python logging module
- **API Documentation**: FastAPI built-in Swagger/OpenAPI

## Project Structure
```
project_root/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration settings
│   ├── db.py                # Database setup & session management
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py       # Request/response logging middleware
│   │   └── exception.py     # Centralized exception handling
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── models.py        # User model
│   │   ├── schemas.py       # Pydantic schemas for auth
│   │   ├── service.py       # Authentication business logic
│   │   └── router.py        # Auth endpoints (register, login)
│   ├── circuit_breaker/
│   │   ├── __init__.py
│   │   └── breaker.py       # Circuit breaker wrapper for external calls
│   └── utils/
│       ├── __init__.py
│       ├── logging.py       # Logging configuration
│       └── exceptions.py    # Custom exception classes
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   ├── test_auth.py         # Auth endpoint tests
│   ├── test_logging.py      # Logging tests
│   └── test_circuit_breaker.py
├── requirements.txt         # Python dependencies
├── pytest.ini               # Pytest configuration
├── .env.example             # Environment variables template
└── README.md                # Project documentation
```

## Coding Conventions
- **Code Style**: Follow PEP 8 (max line length 100 characters)
- **Imports**: Group in order: stdlib → third-party → local imports
- **Naming**:
  - Classes: PascalCase
  - Functions/variables: snake_case
  - Constants: UPPER_SNAKE_CASE
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Use triple-quoted docstrings for modules, classes, and public functions
- **Comments**: Only for non-obvious logic

## Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Start the app
uvicorn app.main:app --reload

# Generate requirements
pip freeze > requirements.txt
```

## Key Patterns
- **Database Sessions**: Use dependency injection with FastAPI's Depends() for SQLAlchemy sessions
- **Request Context**: Store request ID in context for logging correlation
- **Error Responses**: Return consistent JSON error responses with status codes and messages
- **Middleware**: Apply globally for logging and exception handling
- **Environment Variables**: Use .env file for configuration (python-dotenv)
- **API Versioning**: Use URL path prefix (e.g., /api/v1/)
