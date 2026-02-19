# API Specification

## Overview

This document defines the complete API specification for the FastAPI Authentication Service, including all endpoints, request/response schemas, error codes, and examples.

## Base Configuration

- **Base URL**: `http://localhost:8000` (development)
- **API Version**: `v1`
- **Content Type**: `application/json`
- **Authentication**: JWT Bearer tokens
- **Documentation**: `/docs` (Swagger UI), `/redoc` (ReDoc)

## Authentication Flow

### JWT Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "email": "user@example.com",
    "username": "johndoe",
    "exp": 1640995200,
    "iat": 1640991600,
    "jti": "token_unique_id"
  }
}
```

## API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!"
}
```

**Request Schema:**
```python
class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50, regex=r"^[A-Za-z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('password')
    def validate_password_strength(cls, v):
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]", v):
            raise ValueError('Password must contain uppercase, lowercase, digit, and special character')
        return v
```

**Responses:**

**201 Created:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**409 Conflict:**
```json
{
  "detail": "User with this email already exists",
  "error_code": "USER_ALREADY_EXISTS",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must contain uppercase, lowercase, digit, and special character",
      "type": "value_error"
    }
  ]
}
```

#### POST /api/v1/auth/login

Authenticate user and receive access token.

**Request Body:**
```json
{
  "email_or_username": "user@example.com",
  "password": "SecurePass123!"
}
```

**Request Schema:**
```python
class UserLoginRequest(BaseModel):
    email_or_username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)
```

**Responses:**

**200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "refresh_token_here"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid email/username or password",
  "error_code": "INVALID_CREDENTIALS",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**423 Locked:**
```json
{
  "detail": "Account is temporarily locked due to multiple failed attempts",
  "error_code": "ACCOUNT_LOCKED",
  "retry_after": 300,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### POST /api/v1/auth/refresh

Refresh an access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

**Responses:**

**200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired refresh token",
  "error_code": "INVALID_REFRESH_TOKEN",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### POST /api/v1/auth/logout

Logout user and invalidate token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "everywhere": false
}
```

**Responses:**

**200 OK:**
```json
{
  "message": "Successfully logged out",
  "logged_out_sessions": 1
}
```

**200 OK (everywhere: true):**
```json
{
  "message": "Successfully logged out from all devices",
  "logged_out_sessions": 3
}
```

#### GET /api/v1/auth/me

Get current user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Responses:**

**200 OK:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### User Management Endpoints

#### PUT /api/v1/users/me

Update current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "username": "newusername",
  "email": "newemail@example.com"
}
```

**Request Schema:**
```python
class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, regex=r"^[A-Za-z0-9_]+$")
    email: Optional[EmailStr] = Field(None)

    class Config:
        # At least one field must be provided
        @validator('*', pre=True, always=True)
        def check_at_least_one_field(cls, v, values):
            if not any(values.values()) and not v:
                raise ValueError('At least one field must be provided for update')
            return v
```

**Responses:**

**200 OK:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newemail@example.com",
  "username": "newusername",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### PUT /api/v1/users/me/password

Change user password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!",
  "confirm_new_password": "NewPass456!"
}
```

**Responses:**

**200 OK:**
```json
{
  "message": "Password updated successfully",
  "timestamp": "2024-01-15T11:00:00Z"
}
```

**400 Bad Request:**
```json
{
  "detail": "Current password is incorrect",
  "error_code": "INVALID_CURRENT_PASSWORD",
  "timestamp": "2024-01-15T11:00:00Z"
}
```

#### DELETE /api/v1/users/me

Deactivate current user account.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "password": "UserPassword123!",
  "confirmation": "DELETE"
}
```

**Responses:**

**200 OK:**
```json
{
  "message": "Account deactivated successfully",
  "deactivated_at": "2024-01-15T11:00:00Z"
}
```

### Health Check Endpoints

#### GET /health

Basic application health check.

**Responses:**

**200 OK:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

**503 Service Unavailable:**
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### GET /health/detailed

Detailed system health with component status.

**Responses:**

**200 OK:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "up",
      "response_time_ms": 45,
      "connection_pool": {
        "active": 3,
        "idle": 7,
        "total": 10
      }
    },
    "circuit_breaker": {
      "state": "closed",
      "failure_count": 0,
      "success_count": 150,
      "last_failure": null
    },
    "memory": {
      "usage_mb": 128,
      "available_mb": 896
    }
  },
  "uptime_seconds": 86400
}
```

**503 Service Unavailable:**
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "down",
      "error": "Connection timeout after 5 seconds",
      "last_success": "2024-01-15T10:25:00Z"
    },
    "circuit_breaker": {
      "state": "open",
      "failure_count": 5,
      "last_failure": "2024-01-15T10:29:30Z"
    }
  }
}
```

## Error Response Format

### Standard Error Structure

All error responses follow a consistent format:

```json
{
  "detail": "Human readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/auth/login",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request data |
| 400 | `INVALID_CURRENT_PASSWORD` | Current password is incorrect |
| 401 | `INVALID_CREDENTIALS` | Login credentials are invalid |
| 401 | `INVALID_TOKEN` | JWT token is invalid or expired |
| 401 | `INVALID_REFRESH_TOKEN` | Refresh token is invalid |
| 401 | `TOKEN_EXPIRED` | JWT token has expired |
| 403 | `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| 404 | `USER_NOT_FOUND` | Requested user does not exist |
| 409 | `USER_ALREADY_EXISTS` | Email or username already taken |
| 409 | `EMAIL_ALREADY_EXISTS` | Email address already registered |
| 409 | `USERNAME_ALREADY_EXISTS` | Username already taken |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 423 | `ACCOUNT_LOCKED` | Account temporarily locked |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |
| 503 | `DATABASE_UNAVAILABLE` | Database connection failed |
| 503 | `CIRCUIT_BREAKER_OPEN` | Circuit breaker is open |

### Validation Error Format

For 422 Unprocessable Entity responses:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 8}
    }
  ]
}
```

## Rate Limiting

### Default Limits

- **Registration**: 5 attempts per hour per IP
- **Login**: 10 attempts per hour per IP (progressive delay after 3 failures)
- **Password Reset**: 3 attempts per hour per email
- **API Calls (authenticated)**: 1000 requests per hour per user
- **API Calls (unauthenticated)**: 100 requests per hour per IP

### Rate Limit Headers

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 300
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Try again in 300 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 300,
  "limit": 10,
  "window": 3600,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Security Headers

All responses include security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

## CORS Configuration

```http
Access-Control-Allow-Origin: https://your-frontend.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, X-Request-ID
Access-Control-Max-Age: 86400
```

## OpenAPI Schema

### Tags

- **Authentication**: User registration, login, logout, token management
- **Users**: User profile management
- **Health**: System health and monitoring

### Security Schemes

```yaml
securitySchemes:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
    description: "JWT access token obtained from /auth/login"
```

### Example OpenAPI Endpoint

```yaml
paths:
  /api/v1/auth/login:
    post:
      tags:
        - Authentication
      summary: User Login
      description: Authenticate user credentials and return JWT access token
      operationId: login_user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserLoginRequest'
            examples:
              email_login:
                summary: Login with email
                value:
                  email_or_username: "user@example.com"
                  password: "SecurePass123!"
              username_login:
                summary: Login with username
                value:
                  email_or_username: "johndoe"
                  password: "SecurePass123!"
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: Invalid credentials
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '423':
          description: Account locked
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
```

## Example Usage

### cURL Examples

**Register new user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
  }'
```

**Login user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_username": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Get user profile:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Python Client Example

```python
import requests

class AuthClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None

    def register(self, email, username, password):
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "confirm_password": password
            }
        )
        return response.json()

    def login(self, email_or_username, password):
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={
                "email_or_username": email_or_username,
                "password": password
            }
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
        return response.json()

    def get_profile(self):
        response = self.session.get(f"{self.base_url}/api/v1/auth/me")
        return response.json()

# Usage
client = AuthClient()

# Register
client.register("user@example.com", "johndoe", "SecurePass123!")

# Login
client.login("user@example.com", "SecurePass123!")

# Get profile
profile = client.get_profile()
print(profile)
```

This API specification provides comprehensive documentation for all endpoints, error handling, and security considerations for the FastAPI authentication service.