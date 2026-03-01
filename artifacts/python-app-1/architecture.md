# Architecture: Python FastAPI Authentication App

## Overview
A FastAPI application providing user authentication endpoints with JWT token-based security.

## Tech Stack
- **Framework**: FastAPI 0.115+
- **Database**: SQLite (async via aiosqlite)
- **ORM**: SQLAlchemy 2.0+ (async)
- **Authentication**: JWT tokens (python-jose)
- **Password Hashing**: bcrypt (via passlib)
- **Validation**: Pydantic v2
- **Testing**: pytest + httpx

## Entities

### User
- **Fields**:
  - id: int (primary key)
  - email: str (unique, indexed)
  - password_hash: str
  - name: str
  - is_active: bool (default: true)
  - created_at: datetime
  - updated_at: datetime

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user (email, password, name)
- `POST /auth/login` - Login (returns JWT access token)
- `GET /auth/me` - Get current user profile (protected)

### Health
- `GET /health/live` - Liveness check
- `GET /health/ready` - Readiness check (includes DB connectivity)

## Component Design

### Layers
1. **Router Layer** (`app/routers/`) - HTTP request/response handling
2. **Service Layer** (`app/services/`) - Business logic
3. **Repository Pattern** - Database access via SQLAlchemy models
4. **Schema Layer** (`app/schemas/`) - DTOs for request/response

### Security
- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with configurable expiration
- Bearer token authentication on protected endpoints
- Token payload contains user_id in `sub` claim

### Middleware
- CorrelationIdMiddleware - Request tracking
- RequestLoggingMiddleware - HTTP request logging
- CORS - Configurable origins

### Exception Handling
- Custom exceptions: NotFoundException, ConflictException, AuthException
- Global exception handlers return consistent JSON error responses
- Validation errors formatted with field-level details

## Configuration
Environment variables via Pydantic Settings:
- `DATABASE_URL` - SQLite connection string
- `JWT_SECRET` - Secret key for JWT signing (min 32 chars in production)
- `JWT_ALGORITHM` - Algorithm for JWT (default: HS256)
- `JWT_EXPIRATION_MINUTES` - Token expiration time
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed origins
