# Project: FastAPI Auth & Circuit Breaker App

## Tech Stack
- Language: Python 3.12
- Framework: FastAPI 0.110+
- Database: PostgreSQL 16 (prod), SQLite (dev/test via aiosqlite)
- ORM: SQLAlchemy 2.x (async)
- Auth: JWT (python-jose[cryptography]) + passlib[bcrypt]
- API Docs: FastAPI built-in (Swagger UI at /docs, ReDoc at /redoc)
- Migrations: Alembic
- Logging: Python standard logging + JSON formatter (structlog or python-json-logger)
- Build: pip + requirements.txt

## Project Structure

```
app/
├── routers/
│   ├── auth.py              -> POST /auth/register, POST /auth/login
│   ├── users.py             -> GET /users/me, GET /users (admin)
│   └── health.py            -> GET /health/live, GET /health/ready, GET /health/circuit-breakers
├── services/
│   ├── auth_service.py      -> Registration, login, token creation
│   └── user_service.py      -> User CRUD, profile retrieval, listing
├── repositories/
│   └── user_repository.py   -> SQLAlchemy async CRUD for User model
├── models/
│   ├── user.py              -> SQLAlchemy User ORM model
│   └── enums.py             -> Role (USER/ADMIN), CircuitBreakerState enums
├── schemas/
│   ├── auth.py              -> RegisterRequest, LoginRequest, TokenResponse
│   ├── user.py              -> UserResponse, UserListResponse
│   ├── common.py            -> PageResponse, ErrorResponse, ErrorDetail
│   └── health.py            -> HealthResponse, CircuitBreakerStatus
├── core/
│   ├── security.py          -> JWT encode/decode, bcrypt hash/verify
│   ├── circuit_breaker.py   -> CircuitBreaker class (CLOSED/OPEN/HALF_OPEN)
│   └── dependencies.py      -> get_current_user(), require_admin() FastAPI deps
├── middleware/
│   ├── correlation_id.py    -> Assign UUID per request, set X-Correlation-ID header
│   └── logging_middleware.py -> Log method, path, status, latency, correlation_id
├── config.py                -> Pydantic BaseSettings (all env vars)
├── database.py              -> Async engine, session factory, get_db()
├── exceptions.py            -> AppException, AuthException, NotFoundException, etc.
├── exception_handlers.py    -> Global handlers registered on FastAPI app
└── main.py                  -> FastAPI app instantiation, middleware, routers, lifespan

alembic/
├── env.py                   -> Alembic async migration environment
├── versions/                -> Migration scripts
└── alembic.ini              -> Alembic config

requirements.txt             -> Pinned Python dependencies
```

## Commands
- Install: `pip install -r requirements.txt`
- Run: `uvicorn app.main:app --reload`
- Test: `pytest -v --tb=short`
- Lint: `ruff check app/`
- Migrate: `alembic upgrade head`
- Coverage: `pytest --cov=app --cov-report=term-missing`

## Conventions
- Package naming: `app.{module}`
- API endpoints: no `/api/v1/` prefix — endpoints follow spec exactly (`/auth/`, `/users/`, `/health/`)
- Error format: `{"error": {"code": "ERROR_CODE", "message": "Human-readable", "correlation_id": "uuid"}}`
- Validation errors (422): `{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": [...], "correlation_id": "uuid"}}`
- Auth: JWT Bearer token in `Authorization: Bearer <token>` header
- Pagination: `{"items": [...], "total": N, "page": N, "page_size": N}`
- Logging: structured JSON in prod (`APP_ENV=production`), human-readable in dev
- Never log: passwords, tokens, PII, password_hash
- All config from environment variables — no hardcoded secrets
- Async throughout: async def for all route handlers, services, repositories
- SQLAlchemy 2.x style: `select(Model).where(...)`, not legacy query API
