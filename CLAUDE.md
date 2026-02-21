# FastAPI Auth Service - Coding Standards

## Tech Stack
- **Language**: Python 3.9+
- **Framework**: FastAPI
- **Database**: SQLAlchemy with PostgreSQL (primary) / SQLite (development)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Testing**: pytest with pytest-asyncio
- **API Documentation**: Swagger/OpenAPI (built into FastAPI)
- **Logging**: Python logging with structured JSON format
- **Circuit Breaker**: circuitbreaker library
- **Validation**: Pydantic models (built into FastAPI)
- **Environment**: python-dotenv for configuration

## Project Structure
```
auth-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection and session management
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic request/response models
│   ├── api/                 # API route modules
│   │   ├── __init__.py
│   │   ├── auth.py         # Authentication endpoints
│   │   └── users.py        # User management endpoints
│   ├── core/               # Core business logic
│   │   ├── __init__.py
│   │   ├── auth.py         # Authentication logic
│   │   ├── exceptions.py   # Custom exceptions
│   │   └── logging.py      # Logging configuration
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── circuit_breaker.py
│       └── password.py     # Password hashing utilities
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Test configuration and fixtures
│   ├── test_auth.py        # Authentication tests
│   └── test_users.py       # User management tests
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── .env.example            # Environment variables template
└── alembic/                # Database migrations
```

## Coding Conventions
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Import Order**: Standard library, third-party, local imports (separated by blank lines)
- **Formatting**: Black formatter, line length 88 characters
- **Docstrings**: Google style docstrings for functions and classes
- **Type Hints**: Use type hints for all function parameters and return values
- **Async**: Use async/await pattern for all database operations and external calls

## Commands
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest -v
pytest --cov=app tests/

# Run linting
black app/ tests/
flake8 app/ tests/

# Database migrations
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Key Patterns
- **Dependency Injection**: Use FastAPI's dependency injection for database sessions, authentication
- **Error Handling**: Centralized exception handlers with structured error responses
- **Configuration**: Environment-based configuration with Pydantic Settings
- **Database**: SQLAlchemy ORM with async sessions
- **Authentication**: JWT tokens with refresh mechanism
- **Logging**: Structured JSON logging with correlation IDs
- **Testing**: Pytest with async test client and database rollback