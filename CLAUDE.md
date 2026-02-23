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
- **Payment Processing**: Stripe Connect, Global Payouts, ACH/Wire integrations
- **External Systems**: Xactimate/XactAnalysis, EDI 835/837, Document Management

## Project Structure
```
claim-service-2-agent-1/
├── requirements.txt           # Python dependencies
├── app/                      # Main application package
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core configuration and security
│   │   ├── config.py        # Settings and configuration
│   │   ├── security.py      # Authentication and authorization
│   │   └── database.py      # Database connection and session
│   ├── models/              # SQLAlchemy models (implemented)
│   │   ├── __init__.py
│   │   ├── audit.py         # Audit logging models
│   │   ├── claim.py         # Claims data models (comprehensive)
│   │   ├── payment.py       # Payment and disbursement models (complex)
│   │   ├── policy.py        # Policy data models (advanced search)
│   │   └── user.py          # User and role models
│   ├── schemas/             # Pydantic models for API (implemented)
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication schemas
│   │   ├── claim.py         # Claims request/response schemas
│   │   ├── payment.py       # Payment request/response schemas
│   │   └── policy.py        # Policy request/response schemas
│   ├── api/                 # API routes (structure ready, logic needed)
│   │   ├── __init__.py
│   │   ├── deps.py          # API dependencies (auth, db)
│   │   └── v1/              # API version 1
│   │       ├── __init__.py
│   │       ├── auth.py      # Authentication endpoints (basic)
│   │       ├── claims.py    # Claims management endpoints (stubs)
│   │       ├── payments.py  # Payment processing endpoints (stubs)
│   │       └── policies.py  # Policy management endpoints (stubs)
│   ├── services/            # Business logic layer (needs implementation)
│   │   ├── __init__.py
│   │   ├── claim_service.py # Claims business logic (stub)
│   │   ├── payment_service.py # Payment processing logic (stub)
│   │   └── policy_service.py # Policy management logic (stub)
│   └── utils/               # Utility functions (foundational)
│       ├── __init__.py
│       ├── audit.py         # Audit logging utilities
│       ├── integrations.py  # External system integrations (stubs)
│       └── security.py      # Data masking and encryption
├── tests/                   # Test files (basic structure)
│   ├── conftest.py         # Test configuration
│   ├── test_main.py        # Main app tests
│   └── unit/               # Unit tests
├── migrations/              # Alembic migration files (to be created)
├── frontend/                # React frontend (future implementation)
└── artifacts/               # Agent artifacts and analysis
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
- **Error Handling**: Use FastAPI's HTTPException for API errors with specific messages
- **Logging**: Use structlog for structured logging with audit context
- **Documentation**: Clear docstrings and OpenAPI schema examples

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
- **Repository Pattern**: Services layer abstracts database operations with async methods
- **Pydantic Models**: Separate request/response schemas from database models with validation
- **Async Context**: All database operations use async/await patterns with proper session management
- **Audit Trail**: Every data modification includes user_id and timestamp with comprehensive tracking
- **Security**: Sensitive data (SSN/TIN, payments) masked in responses and encrypted at rest
- **Error Responses**: Consistent error format with HTTPException and specific messages per requirements
- **Role-Based Access**: Decorator-based route protection by user role (admin, agent, adjuster)
- **Transaction Management**: Payment operations wrapped in database transactions
- **External Integrations**: Circuit breaker pattern with retry logic for resilience

## Data Architecture Patterns
- **Policy-Claim Relationships**: Foreign key relationships with claim-level policy overrides
- **Payment Complex Structures**: Multiple payees, reserve allocations, void/reversal chains
- **Audit Polymorphism**: Audit trails for all entity types with proper change tracking
- **Search Optimization**: Composite database indexes for performance-critical searches
- **Data Masking**: Consistent masking of PII across all API responses and logs

## Performance Requirements
- **Policy Search**: Results within 3 seconds (9+ search criteria support)
- **Policy/Claim Details**: Load within 5 seconds with full relationship data
- **Payment Processing**: Complete within 5 seconds including external validations
- **Concurrent Sessions**: Support multiple users without performance degradation
- **Database Indexes**: Optimized for search patterns and relationship queries