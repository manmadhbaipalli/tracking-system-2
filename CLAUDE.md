# Project Standards

## Tech Stack
- **Backend**: Python 3.11+ with FastAPI framework
- **Database**: SQLAlchemy 2.0+ with async support
- **Database Engines**: aiosqlite (dev), asyncpg/PostgreSQL (prod)
- **Authentication**: passlib + python-jose for JWT tokens
- **Migration**: Alembic for database migrations
- **Testing**: pytest with pytest-asyncio and pytest-cov
- **Code Quality**: black (formatting), flake8 (linting), mypy (typing)
- **Frontend**: ReactJS (to be implemented)

## Project Structure
```
claim-service-1-agent-1/
├── requirements.txt           # Python dependencies
├── app/                      # Main application package (to be created)
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core configuration and security
│   │   ├── config.py        # Settings and configuration
│   │   ├── security.py      # Authentication and authorization
│   │   └── database.py      # Database connection and session
│   ├── models/              # SQLAlchemy models
│   │   ├── policy.py        # Policy data models
│   │   ├── claim.py         # Claims data models
│   │   ├── payment.py       # Payment and disbursement models
│   │   └── user.py          # User and role models
│   ├── schemas/             # Pydantic models for API
│   │   ├── policy.py        # Policy request/response schemas
│   │   ├── claim.py         # Claims request/response schemas
│   │   └── payment.py       # Payment request/response schemas
│   ├── api/                 # API routes
│   │   ├── v1/              # API version 1
│   │   │   ├── policies.py  # Policy management endpoints
│   │   │   ├── claims.py    # Claims management endpoints
│   │   │   └── payments.py  # Payment processing endpoints
│   │   └── deps.py          # API dependencies (auth, db)
│   ├── services/            # Business logic layer
│   │   ├── policy_service.py
│   │   ├── claim_service.py
│   │   └── payment_service.py
│   └── utils/               # Utility functions
│       ├── audit.py         # Audit logging
│       ├── security.py      # Data masking and encryption
│       └── integrations.py  # External system integrations
├── tests/                   # Test files
├── migrations/              # Alembic migration files
└── frontend/                # React frontend (to be created)
```

## Coding Conventions
- **Python Style**: Follow PEP 8, enforced by black formatter
- **Import Order**: Standard library, third-party, local imports (separated by blank lines)
- **Naming**:
  - snake_case for variables, functions, modules
  - PascalCase for classes and schemas
  - UPPER_CASE for constants
- **Type Hints**: Required for all function signatures and class attributes
- **Async/Await**: Use async patterns throughout for database and external calls
- **Error Handling**: Use FastAPI's HTTPException for API errors
- **Logging**: Use structlog for structured logging with audit context

## Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/

# Database migrations
alembic upgrade head

# Pre-commit hooks (after setup)
pre-commit install
pre-commit run --all-files
```

## Key Patterns
- **Dependency Injection**: Use FastAPI's Depends() for database sessions, auth
- **Repository Pattern**: Services layer abstracts database operations
- **Pydantic Models**: Separate request/response schemas from database models
- **Async Context**: All database operations use async/await patterns
- **Audit Trail**: Every data modification includes user_id and timestamp
- **Security**: Sensitive data (SSN/TIN, payments) masked in responses and encrypted at rest
- **Error Responses**: Consistent error format with HTTPException
- **Role-Based Access**: Decorator-based route protection by user role