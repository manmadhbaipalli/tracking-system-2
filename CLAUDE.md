# Integrated Policy, Claims, and Payments Platform

## Tech Stack
- **Backend Language**: Python 3.11+
- **Backend Framework**: FastAPI
- **Frontend Framework**: ReactJS (to be implemented)
- **Database**: SQLite (development), PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT tokens with passlib for password hashing
- **Documentation**: FastAPI automatic OpenAPI/Swagger docs
- **Testing**: pytest with pytest-asyncio for async tests
- **Logging**: Python standard logging with structured output
- **Validation**: Pydantic models for request/response validation
- **Circuit Breaker**: circuitbreaker library for resilience
- **Payment Integration**: Stripe Connect, Global Payouts, ACH/Wire transfers
- **External Integrations**: Xactimate/XactAnalysis, EDI 835/837, Document Management

## Project Structure
```
claim-processing-platform/
├── app/                    # Main backend application package
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection and session management
│   ├── models/            # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py        # User model (existing)
│   │   ├── policy.py      # Policy model
│   │   ├── claim.py       # Claim model
│   │   ├── payment.py     # Payment model
│   │   └── audit.py       # Audit log model
│   ├── schemas/           # Pydantic models for API
│   │   ├── __init__.py
│   │   ├── user.py        # User request/response models (existing)
│   │   ├── auth.py        # Authentication models (existing)
│   │   ├── policy.py      # Policy schemas
│   │   ├── claim.py       # Claim schemas
│   │   └── payment.py     # Payment schemas
│   ├── api/               # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py        # Authentication endpoints (existing)
│   │   ├── users.py       # User management endpoints (existing)
│   │   ├── policies.py    # Policy management endpoints
│   │   ├── claims.py      # Claims management endpoints
│   │   └── payments.py    # Payment processing endpoints
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py    # Password hashing, JWT tokens (existing)
│   │   ├── exceptions.py  # Custom exceptions (existing)
│   │   ├── circuit_breaker.py # Circuit breaker implementation (existing)
│   │   ├── audit.py       # Audit logging functionality
│   │   ├── payments.py    # Payment processing core
│   │   └── integrations.py # External service integrations
│   ├── services/          # Business logic services
│   │   ├── __init__.py
│   │   ├── policy_service.py    # Policy management business logic
│   │   ├── claim_service.py     # Claims processing business logic
│   │   ├── payment_service.py   # Payment processing business logic
│   │   └── audit_service.py     # Audit service
│   └── utils/             # Utility functions
│       ├── __init__.py
│       ├── logging.py     # Logging configuration (existing)
│       ├── validators.py  # Data validation utilities
│       └── formatters.py  # Data formatting utilities
├── frontend/              # ReactJS frontend (to be created)
│   ├── public/
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client services
│   │   ├── hooks/         # Custom React hooks
│   │   ├── utils/         # Utility functions
│   │   └── types/         # TypeScript type definitions
│   ├── package.json
│   └── tsconfig.json
├── tests/                 # Test files
│   ├── __init__.py
│   ├── conftest.py       # Test configuration and fixtures
│   ├── test_auth.py      # Authentication endpoint tests (existing)
│   ├── test_users.py     # User endpoint tests (existing)
│   ├── test_policies.py  # Policy management tests
│   ├── test_claims.py    # Claims processing tests
│   └── test_payments.py  # Payment processing tests
├── requirements.txt       # Backend dependencies
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
- **Data Masking**: Always mask sensitive data (SSN/TIN, payment information) in responses
- **Audit Trail**: All CRUD operations must be audited with user ID and timestamp
- **Role-Based Access**: Implement proper authorization checks for all endpoints

## Commands
- **Install Backend Dependencies**: `pip install -r requirements.txt`
- **Install Frontend Dependencies**: `cd frontend && npm install`
- **Run Backend Development Server**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run Frontend Development Server**: `cd frontend && npm start`
- **Run Backend Tests**: `pytest -v`
- **Run Backend Tests with Coverage**: `pytest --cov=app --cov-report=html`
- **Format Code**: `black app/ tests/`
- **Lint Code**: `flake8 app/ tests/`
- **Type Check**: `mypy app/`
- **Run Full Application**: Start both backend and frontend servers

## Key Patterns
- **Dependency Injection**: Use FastAPI's Depends() for database sessions and authentication
- **Repository Pattern**: Separate data access logic into repository classes
- **Service Layer**: Business logic in service classes, controllers handle HTTP concerns only
- **Response Models**: Always use Pydantic models for API responses to ensure data validation
- **Exception Handling**: Centralized exception handler middleware for consistent error responses
- **Configuration**: Use environment variables with Pydantic Settings for configuration management
- **Database Sessions**: Use async context managers for database transactions
- **JWT Authentication**: Bearer token authentication with automatic user context injection
- **Circuit Breaker**: Wrap external service calls with circuit breaker pattern for resilience
- **Audit Logging**: All business operations must create audit log entries
- **Data Encryption**: Encrypt sensitive data at rest and in transit
- **PCI Compliance**: Follow PCI-DSS standards for payment data handling
- **Search Optimization**: Support both exact and partial matching for searches
- **Performance**: Response times under 3-5 seconds for all major operations
- **WCAG Compliance**: Ensure accessibility compliance for all UI components