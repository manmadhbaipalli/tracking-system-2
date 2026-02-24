# Project: Auth Service Python 1

## Tech Stack
- Language: Python 3.12
- Framework: FastAPI 0.100+
- Database: PostgreSQL 16 (prod), SQLite (dev)
- ORM: SQLAlchemy 2.0+ with async support
- Auth: JWT access tokens with BCrypt password hashing
- API Docs: FastAPI auto-generated OpenAPI/Swagger
- Migrations: Alembic
- Logging: structlog with JSON formatting
- Validation: Pydantic v2 (built into FastAPI)

## Project Structure
```
app/
├── routers/           # FastAPI endpoints, request validation
│   ├── auth.py        # Registration, login endpoints
│   ├── users.py       # User profile management
│   ├── admin.py       # Admin user management
│   └── health.py      # Health check endpoints
├── services/          # Business logic layer
│   ├── auth_service.py
│   ├── user_service.py
│   ├── admin_service.py
│   └── health_service.py
├── repositories/      # Data access layer
│   ├── user_repository.py
│   └── request_log_repository.py
├── models/            # SQLAlchemy models
│   ├── base.py        # Base model with audit fields
│   ├── user.py        # User entity
│   └── request_log.py # Request audit logs
├── schemas/           # Pydantic request/response schemas
│   ├── auth.py        # Auth-related DTOs
│   ├── user.py        # User profile DTOs
│   ├── admin.py       # Admin operation DTOs
│   └── common.py      # Shared schemas (errors, pagination)
├── utils/             # Utility modules
│   ├── circuit_breaker.py  # Circuit breaker pattern
│   └── logging.py     # Logging configuration
├── config.py          # Pydantic Settings configuration
├── database.py        # SQLAlchemy engine and session config
├── security.py        # JWT, password hashing, auth dependencies
├── exceptions.py      # Custom exceptions and global handler
├── middleware.py      # HTTP middleware (CORS, logging, correlation ID)
└── main.py           # FastAPI app factory
alembic/              # Database migrations
├── versions/         # Migration files
├── env.py           # Alembic async configuration
└── alembic.ini      # Alembic configuration
requirements.txt      # Python dependencies
```

## Commands
- Install: `pip install -r requirements.txt`
- Run Dev: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Test: `pytest tests/ -v --tb=short`
- Migration Create: `alembic revision --autogenerate -m "description"`
- Migration Apply: `alembic upgrade head`
- Format: `black app/ tests/` (if using black formatter)
- Lint: `ruff check app/ tests/` (if using ruff)

## Conventions
- Package naming: `app.{module}`
- API prefix: `/api/v1/`
- Error format: Standardized ErrorResponse with correlation_id
- Auth: JWT Bearer token in Authorization header
- Pagination: Query params `?limit=20&offset=0`, response envelope format
- Logging: Structured JSON in production, readable format in development
- Async/await: Use async for all I/O operations (database, HTTP)
- Type hints: Required for all function signatures and class attributes
- Environment config: All configuration via environment variables, no hardcoded values

## Database Conventions
- Table names: snake_case (users, request_logs)
- Column names: snake_case (created_at, password_hash)
- Primary keys: Integer `id` column, auto-increment
- Foreign keys: `{table}_id` format (user_id references users.id)
- Timestamps: UTC datetime, auto-populated via SQLAlchemy
- Soft deletes: Use `active` boolean flag, not physical deletion
- Indexes: On frequently queried columns (email, active status)

## Security Requirements
- Passwords: BCrypt with cost factor 12, never store plain text
- JWT: HS256 algorithm, configurable expiration (default 24 hours)
- Input validation: All endpoints validate via Pydantic schemas
- CORS: Whitelist specific origins, no wildcards in production
- Rate limiting: 5 failed login attempts per email per hour
- Sensitive data: Never log passwords, tokens, or PII
- SQL injection: Use SQLAlchemy ORM, no raw SQL queries
- Admin endpoints: Require ADMIN role, check in dependency chain

## API Response Standards
- Success responses: Include data in response body
- Error responses: Include status_code, error, message, correlation_id, timestamp
- HTTP status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict), 422 (Validation Error), 503 (Service Unavailable)
- Date format: ISO 8601 UTC (2026-02-24T10:30:00Z)
- Pagination: Use limit/offset query parameters, include total count in response