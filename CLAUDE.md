# Project Standards

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with python-jose
- **Testing**: pytest with pytest-asyncio
- **Documentation**: Swagger/OpenAPI (built into FastAPI)
- **Logging**: Python logging with structured JSON output
- **Circuit Breaker**: circuitbreaker library
- **Validation**: Pydantic (built into FastAPI)

## Project Structure
```
/
├── app/                    # Main application code
│   ├── __init__.py
│   ├── main.py            # FastAPI app entry point
│   ├── core/              # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py      # App configuration
│   │   ├── security.py    # JWT and auth utilities
│   │   ├── logging.py     # Centralized logging setup
│   │   └── exceptions.py  # Custom exceptions and handlers
│   ├── api/               # API endpoints
│   │   ├── __init__.py
│   │   ├── deps.py        # Dependency injection
│   │   └── v1/            # API version 1
│   │       ├── __init__.py
│   │       └── endpoints/ # Individual endpoint modules
│   ├── models/            # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/           # Pydantic models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── services/          # Business logic
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── circuit_breaker.py
│   └── database.py        # Database connection
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py        # pytest configuration
│   ├── test_main.py       # Integration tests
│   └── unit/              # Unit tests
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
├── .env                   # Environment variables (dev)
└── README.md              # Project documentation
```

## Coding Conventions
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Imports**: Standard library → third-party → local imports, sorted alphabetically
- **Formatting**: Black formatter with 88 character line length
- **Type Hints**: Use throughout codebase for better IDE support
- **Docstrings**: Google style for public functions and classes
- **Error Handling**: Use custom exceptions with proper HTTP status codes

## Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
black app/ tests/

# Type checking
mypy app/

# Lint code
flake8 app/ tests/
```

## Key Patterns

### FastAPI App Structure
- Use dependency injection for database sessions and auth
- Separate routers for different API versions
- Use Pydantic models for request/response validation
- Implement middleware for CORS, logging, and exception handling

### Authentication Flow
- JWT tokens with refresh mechanism
- Password hashing with bcrypt
- Role-based access control (if needed)
- Secure cookie storage for tokens

### Error Handling
- Custom exception classes inheriting from HTTPException
- Global exception handlers registered with FastAPI
- Consistent error response format with error codes

### Database Patterns
- Use SQLAlchemy async session
- Implement repository pattern for data access
- Use Alembic for migrations
- Proper transaction handling

### Testing Patterns
- Use pytest fixtures for test database
- Mock external dependencies
- Test both success and failure scenarios
- Integration tests for complete API flows