# API Design: FastAPI Auth & Circuit Breaker App

## Endpoint Inventory

| Method | Path | Description | Auth | Request Schema | Response Schema | Status |
|--------|------|-------------|------|----------------|-----------------|--------|
| POST | /auth/register | Register a new user | No | RegisterRequest (JSON) | RegisterResponse | 201 |
| POST | /auth/login | Authenticate user | No | OAuth2PasswordRequestForm (form) | TokenResponse | 200 |
| GET | /users/me | Get current user profile | JWT (USER\|ADMIN) | — | UserResponse | 200 |
| GET | /users | List all users (paginated) | JWT + ADMIN | Query params | PageResponse[UserResponse] | 200 |
| GET | /health/live | Liveness probe | No | — | LivenessResponse | 200 |
| GET | /health/ready | Readiness probe | No | — | ReadinessResponse | 200/503 |
| GET | /health/circuit-breakers | Circuit breaker states | No | — | dict[str, str] | 200 |

---

## Authentication Scheme

- **Type:** JWT Bearer Token (HS256)
- **Header:** `Authorization: Bearer <token>`
- **Token payload:** `{ "sub": "<user_id>", "email": "<email>", "role": "USER|ADMIN", "exp": <epoch> }`
- **Token lifetime:** Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` env var (default: 60 min)
- **Public endpoints:** `POST /auth/register`, `POST /auth/login`, `GET /health/**`
- **Protected endpoints:** `GET /users/me` (USER+ADMIN), `GET /users` (ADMIN only)
- **Login format:** `OAuth2PasswordRequestForm` (form data: `username=<email>&password=<password>`) for Swagger UI compatibility

---

## Error Response Format

```python
class ErrorDetail(BaseModel):
    field: str
    message: str

class ErrorBody(BaseModel):
    code: str
    message: str
    correlation_id: str
    details: list[ErrorDetail] | None = None

class ErrorResponse(BaseModel):
    error: ErrorBody
```

### HTTP Status → Error Code Mapping

| HTTP Status | Error Code | Scenario |
|-------------|-----------|----------|
| 401 | UNAUTHORIZED | Missing/invalid/expired JWT |
| 403 | FORBIDDEN | Insufficient role or deactivated account |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Duplicate email on registration |
| 422 | VALIDATION_ERROR | Pydantic request validation failure |
| 500 | INTERNAL_ERROR | Unexpected server error |
| 503 | SERVICE_UNAVAILABLE | Circuit breaker OPEN |

### Error Examples

**401 Unauthorized:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid credentials",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**409 Conflict:**
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Email already registered",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**422 Validation Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {"field": "email", "message": "value is not a valid email address"},
      {"field": "password", "message": "String should have at least 8 characters"}
    ],
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## Pagination Envelope

```python
class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int       # 1-based
    page_size: int
```

**Query parameters:**
- `page` — page number, 1-based (default: 1, min: 1)
- `page_size` — items per page (default: 20, min: 1, max: 100)

**Example:**
```json
{
  "items": [...],
  "total": 42,
  "page": 2,
  "page_size": 20
}
```

---

## Request/Response Schemas

### Auth Schemas (`app/schemas/auth.py`)

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
```

### User Schemas (`app/schemas/user.py`)

```python
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
```

### Health Schemas (`app/schemas/health.py`)

```python
class LivenessResponse(BaseModel):
    status: str  # "ok"

class ReadinessResponse(BaseModel):
    status: str  # "ok" | "degraded"
    database: str  # "connected" | "disconnected"
    circuit_breakers: dict[str, str]

class CircuitBreakerStatusResponse(BaseModel):
    name: str
    state: str  # "CLOSED" | "OPEN" | "HALF_OPEN"
    failure_count: int
```

---

## Router Summaries

### Auth Router (`/auth`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | /auth/register | Register a new user account | No |
| POST | /auth/login | Authenticate and receive access token | No |

### Users Router (`/users`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| GET | /users/me | Get current authenticated user profile | JWT |
| GET | /users | List all users with pagination (admin only) | JWT+ADMIN |

### Health Router (`/health`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| GET | /health/live | Liveness probe — always returns 200 ok | No |
| GET | /health/ready | Readiness probe — checks DB and circuit breakers | No |
| GET | /health/circuit-breakers | Returns state of all named circuit breakers | No |

---

## Authorization Matrix

| Endpoint | Public | USER | ADMIN |
|----------|--------|------|-------|
| POST /auth/register | Yes | — | — |
| POST /auth/login | Yes | — | — |
| GET /users/me | — | Yes | Yes |
| GET /users | — | — | Yes |
| GET /health/live | Yes | — | — |
| GET /health/ready | Yes | — | — |
| GET /health/circuit-breakers | Yes | — | — |
| GET /docs, /redoc, /openapi.json | Yes* | — | — |

*Disabled when `DOCS_ENABLED=false`

---

## Health Endpoints

```
GET /health/live   → 200 {"status": "ok"}                              (liveness)
GET /health/ready  → 200/503 {"status": "ok|degraded", "database": "connected|disconnected", "circuit_breakers": {...}} (readiness)
GET /health/circuit-breakers → 200 {"database": "CLOSED", ...}         (CB states)
```
