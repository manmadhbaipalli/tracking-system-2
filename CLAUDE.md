# Project: Integrated Policy, Claims, and Payments Platform

## Technology Stack
- **Backend**: Python 3.11+, FastAPI
- **Database**: SQLAlchemy (async), SQLite (dev), PostgreSQL (prod)
- **Authentication**: JWT with Bearer tokens
- **Validation**: Pydantic v2

## Package Structure
```
app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── config.py            # Pydantic Settings
├── database.py          # SQLAlchemy engine and session
├── security.py          # JWT and password hashing
├── exceptions.py        # Custom exceptions
├── middleware.py        # CORS, logging, correlation ID
├── models/              # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── policy.py
│   ├── claim.py
│   └── payment.py
├── schemas/             # Pydantic request/response models
│   ├── __init__.py
│   ├── auth.py
│   ├── user.py
│   ├── policy.py
│   ├── claim.py
│   └── payment.py
├── routers/             # FastAPI route handlers
│   ├── __init__.py
│   ├── auth.py
│   ├── policy.py
│   ├── claim.py
│   └── payment.py
└── services/            # Business logic layer
    ├── __init__.py
    ├── auth_service.py
    ├── policy_service.py
    ├── claim_service.py
    └── payment_service.py
```

## Code Style
- Use async/await for all I/O operations
- Type hints required on all function signatures
- Use Pydantic for validation
- Follow PEP 8 naming conventions
- Service layer pattern: Router → Service → Repository (direct SQLAlchemy queries in services)
- No business logic in routes
- Log all business-significant actions

## Security Standards
- Mask SSN/TIN in responses (show only last 4 digits)
- Encrypt sensitive data at rest
- All payment data PCI-DSS compliant
- JWT tokens expire after 60 minutes (configurable)
- Password hashing with bcrypt
- Role-based access control

## Audit Requirements
- Log all actions with user_id and timestamp
- Track all changes to policy, claim, and payment data
- Maintain immutable audit trail

## Build & Run Commands
```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run (development)
uvicorn app.main:app --reload --port 8000

# Database migrations
alembic revision --autogenerate -m "message"
alembic upgrade head
```

## API Documentation
- OpenAPI/Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables
See `.env.example` for required configuration.
