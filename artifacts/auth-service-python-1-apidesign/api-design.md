# API Design: Auth Service Python 1

## Endpoint Inventory

| Method | Path | Description | Auth | Request Schema | Response Schema | Status |
|--------|------|-------------|------|----------------|-----------------|--------|
| POST | /api/v1/auth/register | Register new user | No | RegisterRequest | AuthResponse | 201 |
| POST | /api/v1/auth/login | Authenticate user | No | LoginRequest | AuthResponse | 200 |
| GET | /api/v1/users/me | Get current user profile | JWT | — | UserResponse | 200 |
| PUT | /api/v1/users/me | Update current user profile | JWT | UserUpdateRequest | UserResponse | 200 |
| PUT | /api/v1/users/me/password | Change current user password | JWT | PasswordChangeRequest | — | 204 |
| GET | /api/v1/admin/users | List all users (paginated) | JWT+ADMIN | Query params | PageResponse[UserResponse] | 200 |
| PUT | /api/v1/admin/users/{id}/role | Update user role | JWT+ADMIN | RoleUpdateRequest | UserResponse | 200 |
| PUT | /api/v1/admin/users/{id}/status | Update user active status | JWT+ADMIN | StatusUpdateRequest | UserResponse | 200 |
| GET | /health/live | Liveness probe | No | — | HealthResponse | 200 |
| GET | /health/ready | Readiness probe | No | — | HealthResponse | 200 |

---

## Authentication Scheme

- **Type:** JWT Bearer Token
- **Header:** `Authorization: Bearer <token>`
- **Token lifetime:** 86400 seconds (24 hours, configurable via `JWT_EXPIRATION_SECONDS`)
- **Token payload:** `{"sub": user_id, "email": "user@example.com", "role": "USER", "iat": ..., "exp": ...}`
- **Signing algorithm:** HS256 with configurable secret key
- **Public endpoints:** `/api/v1/auth/**`, `/health/**`, `/docs`, `/openapi.json`

---

## Error Response Format

```python
class ErrorResponse(BaseModel):
    status: int
    error: str
    message: str
    details: list[FieldError] | None = None
    timestamp: datetime

class FieldError(BaseModel):
    field: str
    message: str
```

### Error Examples

**400 Bad Request (Validation):**
```json
{
  "status": 400,
  "error": "Bad Request",
  "message": "Validation failed",
  "details": [
    {"field": "email", "message": "value is not a valid email address"},
    {"field": "password", "message": "String should have at least 8 characters"}
  ],
  "timestamp": "2026-02-24T10:30:00Z"
}
```

**401 Unauthorized:**
```json
{"status": 401, "error": "Unauthorized", "message": "Invalid or expired token", "details": null, "timestamp": "2026-02-24T10:30:00Z"}
```

**403 Forbidden:**
```json
{"status": 403, "error": "Forbidden", "message": "Admin role required", "details": null, "timestamp": "2026-02-24T10:30:00Z"}
```

**404 Not Found:**
```json
{"status": 404, "error": "Not Found", "message": "User not found with id: 999", "details": null, "timestamp": "2026-02-24T10:30:00Z"}
```

**409 Conflict:**
```json
{"status": 409, "error": "Conflict", "message": "Email already exists", "details": null, "timestamp": "2026-02-24T10:30:00Z"}
```

---

## Pagination Envelope (MANDATORY for all list endpoints)

```python
class PageResponse(BaseModel, Generic[T]):
    content: list[T]
    page: int
    size: int
    total_elements: int
    total_pages: int
    first: bool
    last: bool
```

**Query parameters:** `?page=0&size=20` (0-based indexing, default size=20, max size=100)

**Example Response:**
```json
{
  "content": [{"id": 1, "email": "user@example.com", ...}, ...],
  "page": 0,
  "size": 20,
  "total_elements": 150,
  "total_pages": 8,
  "first": true,
  "last": false
}
```

---

## Request/Response Schemas

### Authentication Schemas (app/schemas/auth.py)

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="User password")
    full_name: str = Field(min_length=1, max_length=100, description="User full name")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, description="User password")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
```

### User Schemas (app/schemas/user.py)

```python
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, description="Current password")
    new_password: str = Field(min_length=8, max_length=128, description="New password")
```

### Admin Schemas (app/schemas/admin.py)

```python
class RoleUpdateRequest(BaseModel):
    role: UserRole

class StatusUpdateRequest(BaseModel):
    active: bool

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str | None = None
    circuit_breaker: str | None = None
```

---

## Router Implementation Details

### Authentication Router (app/routers/auth.py)

- **POST /api/v1/auth/register**: Create new user account
  - Request validation: email format, password strength, name length
  - Business logic: email uniqueness check, password hashing, JWT generation
  - Response: 201 Created with JWT token and expiration
  - Errors: 409 if email exists, 400 for validation failures

- **POST /api/v1/auth/login**: Authenticate existing user
  - Request validation: email format, password presence
  - Business logic: email lookup, password verification, JWT generation
  - Response: 200 OK with JWT token and expiration
  - Errors: 401 for invalid credentials, 400 for validation failures

### Users Router (app/routers/users.py)

- **GET /api/v1/users/me**: Get current user profile
  - Authentication: JWT required
  - Response: 200 OK with UserResponse (no sensitive fields)
  - Errors: 401 if token invalid

- **PUT /api/v1/users/me**: Update current user profile
  - Authentication: JWT required
  - Request validation: optional email format, name length
  - Business logic: email uniqueness check if changed
  - Response: 200 OK with updated UserResponse
  - Errors: 401 if token invalid, 409 if email exists, 400 for validation

- **PUT /api/v1/users/me/password**: Change password
  - Authentication: JWT required
  - Request validation: current password, new password strength
  - Business logic: verify current password, hash new password
  - Response: 204 No Content
  - Errors: 401 if token invalid, 400 if current password wrong

### Admin Router (app/routers/admin.py)

- **GET /api/v1/admin/users**: List all users with pagination
  - Authentication: JWT + ADMIN role required
  - Query params: page (default 0), size (default 20, max 100)
  - Response: 200 OK with PageResponse[UserResponse]
  - Errors: 401 if token invalid, 403 if not admin

- **PUT /api/v1/admin/users/{id}/role**: Update user role
  - Authentication: JWT + ADMIN role required
  - Path param: user ID
  - Request validation: role enum (USER/ADMIN)
  - Response: 200 OK with updated UserResponse
  - Errors: 401/403 for auth, 404 if user not found, 400 for validation

- **PUT /api/v1/admin/users/{id}/status**: Activate/deactivate user
  - Authentication: JWT + ADMIN role required
  - Path param: user ID
  - Request validation: active boolean
  - Business logic: prevent self-deactivation
  - Response: 200 OK with updated UserResponse
  - Errors: 401/403 for auth, 404 if user not found, 400 if self-deactivation

### Health Router (app/routers/health.py)

- **GET /health/live**: Liveness probe
  - No authentication required
  - Simple health check - returns 200 if app is running
  - Response: 200 OK with HealthResponse
  - Response time: < 100ms

- **GET /health/ready**: Readiness probe
  - No authentication required
  - Comprehensive health check: database connectivity, circuit breaker status
  - Response: 200 OK if ready, 503 if not ready
  - Response time: < 500ms

---

## Rate Limiting Strategy

- **Failed login attempts:** 5 attempts per email per hour
- **Token refresh:** Not applicable (stateless JWT)
- **API rate limiting:** Implemented at API gateway/reverse proxy level
- **Per-user limits:** Not implemented at application level

---

## API Versioning Strategy

- **URL-based versioning:** `/api/v1/` prefix
- **Backward compatibility:** Maintained within major versions
- **OpenAPI specification:** Version matches API version
- **Future versions:** `/api/v2/` for breaking changes

---

## Health Endpoints (created by SmartDev, documented here)

```
GET /health/live   → {"status": "healthy", "timestamp": "2026-02-24T10:30:00Z"}
GET /health/ready  → {"status": "healthy", "timestamp": "2026-02-24T10:30:00Z", "database": "connected", "circuit_breaker": "closed"}
```