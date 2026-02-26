# Architecture: Simple Python App

## Tech Stack
- **Framework:** FastAPI
- **Database:** SQLite (async via aiosqlite)
- **ORM:** SQLAlchemy 2.x (async)
- **Auth:** JWT (python-jose) + bcrypt (passlib)
- **Validation:** Pydantic v2

## Entities
### User
- id (int, PK)
- email (str, unique)
- name (str)
- password_hash (str)
- created_at (datetime)
- is_active (bool)

## API Endpoints
- POST /auth/register — register new user
- POST /auth/login — login, get JWT token
- GET /users/me — get current user profile
- PUT /users/me — update current user profile
- GET /health/live — liveness check
- GET /health/ready — readiness check (DB ping)

## Component Design
- **Router layer:** HTTP handling, input validation
- **Service layer:** business logic, exception throwing
- **Repository layer:** database queries
- **Middleware:** correlation ID propagation, request logging
