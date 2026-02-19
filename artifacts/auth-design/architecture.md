# Auth System Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENT APPLICATIONS                          │
│                  (Web, Mobile, Desktop, Third-party APIs)               │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTP/HTTPS Requests
                             │ (REST API)
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Middleware Chain                              │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │ 1. RequestIDMiddleware (Add unique request ID)          │    │   │
│  │  │    → Generates UUID, stores in request.state            │    │   │
│  │  │    → Returns X-Request-ID header                        │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │ 2. LoggingMiddleware (Structured JSON logging)          │    │   │
│  │  │    → Logs: method, path, status, response_time          │    │   │
│  │  │    → Includes request_id for traceability               │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │ 3. ExceptionHandlerMiddleware (Catch all exceptions)    │    │   │
│  │  │    → Returns consistent JSON error format               │    │   │
│  │  │    → No stack traces to client (logged server-side)     │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │ 4. CORSMiddleware (Handle cross-origin requests)        │    │   │
│  │  │    → Restrict to configured origins                     │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                 │                                        │
│                                 ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Route Handlers                              │   │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐    │   │
│  │  │ Health Routes   │  │ Auth Routes  │  │ User Routes     │    │   │
│  │  │ GET /health     │  │ POST /login  │  │ GET /profile    │    │   │
│  │  │                 │  │ POST /register│ │ (Protected)     │    │   │
│  │  │                 │  │ POST /refresh│ │                 │    │   │
│  │  └────────────────┬┘  └──────┬───────┘  └────────┬────────┘    │   │
│  │                   │          │                   │             │   │
│  │                   └──────────┼───────────────────┘             │   │
│  │                              ▼                                 │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │           Dependency Injection (FastAPI Depends)        │ │   │
│  │  │  ┌─────────────────┐  ┌──────────────┐  ┌────────────┐ │ │   │
│  │  │  │ get_db()        │  │get_current   │  │get_logger()│ │ │   │
│  │  │  │ - AsyncSession  │  │_user()       │  │ - Logger   │ │ │   │
│  │  │  │                 │  │ - Validates  │  │            │ │ │   │
│  │  │  │                 │  │   JWT token  │  │            │ │ │   │
│  │  │  │                 │  │ - Returns    │  │            │ │ │   │
│  │  │  │                 │  │   User obj   │  │            │ │ │   │
│  │  │  └─────────────────┘  └──────────────┘  └────────────┘ │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  │                         │                                      │   │
│  │                         ▼                                      │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │                  Service Layer                           │ │   │
│  │  │  ┌────────────────────┐  ┌─────────────────────────┐   │ │   │
│  │  │  │  AuthService       │  │    UserService          │   │ │   │
│  │  │  │                    │  │                         │   │ │   │
│  │  │  │ • register_user()  │  │ • create_user()        │   │ │   │
│  │  │  │ • login_user()     │  │ • get_user_by_email()  │   │ │   │
│  │  │  │ • refresh_token()  │  │ • get_user_by_id()     │   │ │   │
│  │  │  │ • validate_pwd()   │  │ • get_user_by_user..() │   │ │   │
│  │  │  │                    │  │ • update_last_login()  │   │ │   │
│  │  │  └────────────────────┘  └─────────────────────────┘   │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  │                         │                                      │   │
│  │                         ▼                                      │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │                   Utility Layer                          │ │   │
│  │  │  ┌────────────┐  ┌───────────┐  ┌──────────────┐        │ │   │
│  │  │  │JWT Utils   │  │Password   │  │CircuitBreaker│       │ │   │
│  │  │  │            │  │Utils      │  │              │       │ │   │
│  │  │  │• create_   │  │• hash_pwd │  │ • Decorator  │       │ │   │
│  │  │  │  access_   │  │• verify_  │  │ • Track fail │       │ │   │
│  │  │  │  token()   │  │  pwd()    │  │ • State mgmt │       │ │   │
│  │  │  │• create_   │  │           │  │ (C/O/H-O)   │       │ │   │
│  │  │  │  refresh_  │  │           │  │              │       │ │   │
│  │  │  │  token()   │  │           │  │              │       │ │   │
│  │  │  │• decode_   │  │           │  │              │       │ │   │
│  │  │  │  token()   │  │           │  │              │       │ │   │
│  │  │  └────────────┘  └───────────┘  └──────────────┘        │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  │                         │                                      │   │
│  │                         ▼                                      │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │              Exception Handling                          │ │   │
│  │  │  ┌────────────────────────────────────────────────────┐ │ │   │
│  │  │  │ Custom Exception Hierarchy                         │ │ │   │
│  │  │  │ • AuthException (401)                              │ │ │   │
│  │  │  │   - InvalidCredentialsException                    │ │ │   │
│  │  │  │   - TokenExpiredException                          │ │ │   │
│  │  │  │   - TokenInvalidException                          │ │ │   │
│  │  │  │ • ValidationException (400)                        │ │ │   │
│  │  │  │   - DuplicateEmailException                        │ │ │   │
│  │  │  │   - DuplicateUsernameException                     │ │ │   │
│  │  │  │   - WeakPasswordException                          │ │ │   │
│  │  │  │ • CircuitBreakerOpenException (503)                │ │ │   │
│  │  │  └────────────────────────────────────────────────────┘ │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │ DB Queries
                              │ Async SQL
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Data Access Layer                                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │         SQLAlchemy ORM + Async Session Management               │   │
│  │                                                                  │   │
│  │  Models:                                                         │   │
│  │  • User(id, username, email, hashed_password, is_active,       │   │
│  │         created_at, updated_at, last_login)                    │   │
│  │                                                                  │   │
│  │  Database Drivers:                                              │   │
│  │  • aiosqlite (for SQLite - development)                        │   │
│  │  • asyncpg (for PostgreSQL - production)                       │   │
│  │                                                                  │   │
│  │  Connection Pool:                                               │   │
│  │  • Size: 20 connections (configurable)                         │   │
│  │  • Echo: Debug mode logs all SQL                               │   │
│  │  • Timeout: Configurable connection timeout                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │ SQL Queries
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Database                                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Development: SQLite (file-based, no setup required)            │   │
│  │  Production:  PostgreSQL (separate server, managed backups)     │   │
│  │                                                                  │   │
│  │  Tables:                                                         │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │ users                                                      │ │   │
│  │  │  • id (PRIMARY KEY)                                        │ │   │
│  │  │  • username (UNIQUE, INDEXED)                             │ │   │
│  │  │  • email (UNIQUE, INDEXED)                                │ │   │
│  │  │  • hashed_password                                         │ │   │
│  │  │  • is_active (default: true)                              │ │   │
│  │  │  • created_at (timestamp)                                 │ │   │
│  │  │  • updated_at (timestamp)                                 │ │   │
│  │  │  • last_login (nullable)                                  │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  │                                                                  │   │
│  │  Future Tables:                                                 │   │
│  │  • refresh_tokens (for token revocation)                       │   │
│  │  • audit_logs (for compliance)                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Interaction Flows

### Registration Flow

```
User Client
   │
   ├─ POST /api/auth/register
   │  {email, username, password}
   │
   ▼
FastAPI Router
   │
   ├─ Pydantic validates input
   ├─ Raises ValidationException if invalid
   │
   ▼
AuthService.register_user()
   │
   ├─ Validate password strength
   ├─ Raise WeakPasswordException if too weak
   │
   ├─ UserService.get_user_by_email() [check exists]
   ├─ Raise DuplicateEmailException if exists
   │
   ├─ UserService.get_user_by_username() [check exists]
   ├─ Raise DuplicateUsernameException if exists
   │
   ├─ PasswordUtils.hash_password()
   │  [bcrypt hash with salt]
   │
   ├─ UserService.create_user()
   │  [Insert into database]
   │
   ├─ JWTUtils.create_access_token()
   │  [Generate JWT with 30 min expiration]
   │
   ├─ JWTUtils.create_refresh_token()
   │  [Generate JWT with 7 day expiration]
   │
   ├─ Log: "User registered successfully" [without password]
   │
   ▼
Return TokenResponse
   ├─ access_token
   ├─ refresh_token
   ├─ token_type: "bearer"
   └─ user: {id, email, username, is_active, created_at, last_login}

   ▼
Client receives 201 Created
```

---

### Login Flow

```
User Client
   │
   ├─ POST /api/auth/login
   │  {email, password}
   │
   ▼
FastAPI Router
   │
   ├─ Pydantic validates input
   │
   ▼
AuthService.login_user()
   │
   ├─ UserService.get_user_by_email()
   ├─ Raise UserNotFoundException if not found
   │
   ├─ PasswordUtils.verify_password()
   ├─ Raise InvalidCredentialsException if wrong
   │
   ├─ Update user.last_login = now()
   │
   ├─ JWTUtils.create_access_token()
   │
   ├─ JWTUtils.create_refresh_token()
   │
   ├─ Log: "User logged in successfully" [with user_id, not password]
   │
   ▼
Return TokenResponse
   ├─ access_token
   ├─ refresh_token
   ├─ token_type: "bearer"
   └─ user: {id, email, username, is_active, created_at, last_login}

   ▼
Client receives 200 OK
```

---

### Protected Route Access Flow

```
User Client
   │
   ├─ GET /api/user/profile
   │  Header: Authorization: Bearer {access_token}
   │
   ▼
FastAPI Router
   │
   ├─ Dependency: get_current_user()
   │
   ├─ Extract token from "Bearer {token}" format
   │ [Raise TokenInvalidException if missing]
   │
   ├─ JWTUtils.decode_token()
   │  ├─ Verify signature using JWT_SECRET_KEY
   │  ├─ Raise TokenInvalidException if invalid signature
   │  ├─ Raise TokenExpiredException if expired
   │  └─ Return payload with user_id
   │
   ├─ UserService.get_user_by_id(user_id)
   │ [Raise UserNotFoundException if not found]
   │
   ├─ Inject User object into route handler
   │
   ▼
Route Handler
   │
   ├─ Access current_user object
   ├─ Return user data
   │
   ▼
Client receives 200 OK with user data
```

---

### Token Refresh Flow

```
User Client
   │
   ├─ POST /api/auth/refresh
   │  {refresh_token}
   │
   ▼
FastAPI Router
   │
   ├─ Pydantic validates input
   │
   ▼
AuthService.refresh_access_token()
   │
   ├─ JWTUtils.decode_token(refresh_token)
   │  ├─ Verify signature
   │  ├─ Raise TokenInvalidException if invalid signature
   │  ├─ Raise TokenExpiredException if expired
   │  └─ Return payload with user_id
   │
   ├─ UserService.get_user_by_id(user_id)
   │  [Raise UserNotFoundException if not found]
   │
   ├─ JWTUtils.create_access_token()
   │  [New access token with 30 min expiration]
   │
   ├─ JWTUtils.create_refresh_token()
   │  [New refresh token with 7 day expiration]
   │
   ├─ Log: "Token refreshed successfully"
   │
   ▼
Return TokenResponse
   ├─ access_token (new)
   ├─ refresh_token (new)
   ├─ token_type: "bearer"
   └─ user: {id, email, username, is_active, created_at, last_login}

   ▼
Client receives 200 OK
```

---

### Error Handling Flow

```
Any Route Handler
   │
   ├─ Raises Exception (custom or built-in)
   │  (e.g., DuplicateEmailException, TokenExpiredException, etc.)
   │
   ▼
ExceptionHandlerMiddleware
   │
   ├─ Catch exception
   │
   ├─ Map exception to HTTP status code
   │  (InvalidCredentialsException → 401)
   │  (DuplicateEmailException → 400)
   │  (CircuitBreakerOpenException → 503)
   │
   ├─ Log exception details
   │  ├─ Timestamp
   │  ├─ Request ID
   │  ├─ Exception type
   │  ├─ Stack trace (server-side only)
   │  ├─ User context (if available)
   │  └─ Level: WARNING or ERROR
   │
   ├─ Create response
   │  ├─ detail: User-friendly message
   │  ├─ error_code: Machine-readable code
   │  ├─ status_code: HTTP status
   │  ├─ timestamp: ISO format
   │  └─ request_id: For correlation
   │
   ▼
Return JSON response to client
   │
   ├─ No stack traces (security)
   ├─ Clear error code for client handling
   ├─ Request ID for support reference
   │
   ▼
Client receives error with status code
```

---

## Data Model Relationships

```
┌──────────────────────┐
│      User (ORM)      │
├──────────────────────┤
│ id (INT, PK)         │
│ username (STR, UNQ)  │
│ email (STR, UNQ)     │
│ hashed_password      │
│ is_active (BOOL)     │
│ created_at (DT)      │
│ updated_at (DT)      │
│ last_login (DT, NUL) │
└──────────────────────┘
         │
         │ 1:Many (Future)
         │
    ┌────▼────────────────────────┐
    │  RefreshToken (Future)       │
    ├──────────────────────────────┤
    │ id (INT, PK)                 │
    │ user_id (INT, FK) ───────────┼──→ User.id
    │ token_hash (STR, UNQ)        │
    │ expires_at (DT)              │
    │ is_revoked (BOOL)            │
    │ created_at (DT)              │
    └──────────────────────────────┘

    ┌──────────────────────────────┐
    │  AuditLog (Future)           │
    ├──────────────────────────────┤
    │ id (INT, PK)                 │
    │ user_id (INT, FK, NUL) ──────┼──→ User.id
    │ action (STR)                 │
    │ resource (STR)               │
    │ details (JSON)               │
    │ ip_address (STR)             │
    │ user_agent (STR)             │
    │ created_at (DT)              │
    └──────────────────────────────┘
```

---

## Request/Response Cycle with Logging

```
HTTP Request
    │
    ├─ [1] RequestIDMiddleware
    │      └─ Generate UUID → request.state.request_id
    │
    ├─ [2] LoggingMiddleware (Before Route)
    │      └─ Log START:
    │         {
    │           "timestamp": "2026-02-19T10:30:45.123Z",
    │           "level": "INFO",
    │           "message": "Request started",
    │           "request_id": "abc123",
    │           "method": "POST",
    │           "path": "/api/auth/login",
    │           "client_ip": "192.168.1.1"
    │         }
    │
    ├─ [3] ExceptionHandlerMiddleware (Wrapper)
    │      │
    │      ├─ Route Handler
    │      │  ├─ Dependencies injected (get_db, get_current_user, get_logger)
    │      │  ├─ Business logic executes
    │      │  └─ Service methods called
    │      │       └─ Log: "User logged in successfully"
    │      │          {
    │      │            "timestamp": "...",
    │      │            "level": "INFO",
    │      │            "message": "User logged in successfully",
    │      │            "request_id": "abc123",
    │      │            "user_id": 123,
    │      │            "module": "auth_service"
    │      │          }
    │      │
    │      └─ Returns Response (Success or Exception)
    │
    ├─ [4] LoggingMiddleware (After Route)
    │      └─ Log END:
    │         {
    │           "timestamp": "2026-02-19T10:30:45.234Z",
    │           "level": "INFO",
    │           "message": "Request completed",
    │           "request_id": "abc123",
    │           "status_code": 200,
    │           "duration_ms": 111
    │         }
    │
    ├─ [5] Add Response Headers
    │      └─ X-Request-ID: abc123
    │
    ▼
HTTP Response with headers and body
```

---

## Error Handling with Logging Example

```
POST /api/auth/register
{
  "email": "john@example.com",
  "username": "john",
  "password": "weak"  ← Too weak
}
    │
    ├─ [1] RequestIDMiddleware
    │      └─ request_id = "xyz789"
    │
    ├─ [2] LoggingMiddleware (Before)
    │      └─ Log: Request started
    │
    ├─ [3] Route Handler
    │      │
    │      ├─ AuthService.register_user()
    │      │  ├─ Validate password strength
    │      │  └─ ✗ RAISE WeakPasswordException
    │      │       message: "Password must contain uppercase, lowercase, digit, special char"
    │      │       error_code: "WEAK_PASSWORD"
    │      │       status_code: 400
    │      │
    │      └─ Exception caught by ExceptionHandlerMiddleware
    │
    ├─ [4] ExceptionHandlerMiddleware
    │      │
    │      ├─ LOG ERROR (server-side)
    │      │  {
    │      │    "timestamp": "2026-02-19T10:30:45.123Z",
    │    │    "level": "WARNING",
    │      │    "message": "Validation error during registration",
    │      │    "request_id": "xyz789",
    │      │    "exception_type": "WeakPasswordException",
    │      │    "error_code": "WEAK_PASSWORD",
    │      │    "stack_trace": "...[full stack]..."  ← Server-side only
    │      │  }
    │      │
    │      └─ Return JSON Response (no stack trace to client)
    │         {
    │           "detail": "Password must contain uppercase, lowercase, digit, special char",
    │           "error_code": "WEAK_PASSWORD",
    │           "status_code": 400,
    │           "timestamp": "2026-02-19T10:30:45.123Z",
    │           "request_id": "xyz789"
    │         }
    │         HTTP Status: 400 Bad Request
    │
    ├─ [5] LoggingMiddleware (After)
    │      └─ Log: Request completed
    │         {
    │           "timestamp": "2026-02-19T10:30:45.234Z",
    │           "level": "INFO",
    │           "message": "Request completed",
    │           "request_id": "xyz789",
    │           "status_code": 400,
    │           "duration_ms": 111
    │         }
    │
    ▼
HTTP Response 400
```

---

## Deployment Architecture

### Development Environment

```
Developer Machine
    │
    ├─ Python 3.10+ virtual environment
    ├─ FastAPI with uvicorn --reload
    ├─ SQLite database (file: ./test.db)
    ├─ Logs to console (DEBUG level)
    ├─ No CORS restrictions (allow all)
    └─ JWT_SECRET_KEY: development-key-not-secure
```

### Production Environment

```
┌────────────────────────────────────────────────┐
│              Kubernetes Cluster                │
│  ┌──────────────────────────────────────────┐  │
│  │  Load Balancer / Reverse Proxy           │  │
│  │  (nginx, CloudFlare, etc.)               │  │
│  │  ├─ HTTPS termination                    │  │
│  │  ├─ Rate limiting                        │  │
│  │  └─ DDoS protection                      │  │
│  └──────────────────────────────────────────┘  │
│              │                                  │
│              ▼                                  │
│  ┌──────────────────────────────────────────┐  │
│  │   FastAPI Service Replicas (3+)          │  │
│  │   ┌────────────────────────────────────┐ │  │
│  │   │ Pod 1: FastAPI + uvicorn          │ │  │
│  │   │ - Dockerfile deployment            │ │  │
│  │   │ - Environment from ConfigMap       │ │  │
│  │   │ - Secrets for JWT key              │ │  │
│  │   └────────────────────────────────────┘ │  │
│  │   ┌────────────────────────────────────┐ │  │
│  │   │ Pod 2: FastAPI + uvicorn          │ │  │
│  │   │ (replicated)                       │ │  │
│  │   └────────────────────────────────────┘ │  │
│  │   ┌────────────────────────────────────┐ │  │
│  │   │ Pod N: FastAPI + uvicorn          │ │  │
│  │   │ (replicated)                       │ │  │
│  │   └────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────┘  │
│              │                                  │
│              ▼                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  PostgreSQL Database (Managed)           │  │
│  │  ├─ Cloud provider managed DB            │  │
│  │  │  (AWS RDS, GCP Cloud SQL, etc.)      │  │
│  │  ├─ Automated backups                    │  │
│  │  ├─ Multi-region replication             │  │
│  │  ├─ SSL/TLS connections                  │  │
│  │  └─ Connection pooling (PgBouncer)       │  │
│  └──────────────────────────────────────────┘  │
│              │                                  │
│              ▼                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Centralized Logging                    │  │
│  │  ├─ ELK Stack / Datadog / Splunk        │  │
│  │  ├─ Receives JSON logs from all pods    │  │
│  │  ├─ Indexed by request_id               │  │
│  │  └─ Searchable and alertable            │  │
│  └──────────────────────────────────────────┘  │
│              │                                  │
│              ▼                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Monitoring & Alerting                  │  │
│  │  ├─ Prometheus metrics                  │  │
│  │  ├─ Grafana dashboards                  │  │
│  │  ├─ PagerDuty/Opsgenie alerts           │  │
│  │  └─ Health check: /health endpoint      │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

---

## Security Boundaries

```
┌─────────────────────────────────────────────────┐
│           Untrusted Client Input                │
│                                                 │
│  • HTTP request body (JSON)                    │
│  • HTTP headers (Authorization, etc.)          │
│  • Query parameters                            │
│  • URL path parameters                         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Pydantic Validation │ ← Validation Boundary
        └────────────────────┘
                 │
                 ▼ (Trusted data)
        ┌────────────────────┐
        │  Route Handlers    │
        │  & Services        │
        └────────────────────┘
                 │
                 ▼ (Parameterized queries)
        ┌────────────────────┐
        │  SQLAlchemy ORM    │ ← SQL Injection Protection
        │  (No raw SQL)      │
        └────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  PostgreSQL        │ ← Trusted data only
        │  Database          │
        └────────────────────┘

┌─────────────────────────────────────────────────┐
│       JWT Token Validation Boundary             │
│                                                 │
│  Untrusted: Token from client (could be forged)│
│  │                                              │
│  ▼                                              │
│  JWTUtils.decode_token()                       │
│  ├─ Verify signature with JWT_SECRET_KEY       │
│  │  (Only server knows secret)                 │
│  ├─ Check expiration                           │
│  ├─ Validate standard claims                   │
│  │  (iss, aud, sub, exp, iat)                 │
│  │                                              │
│  ▼ (Signature verified = Trusted)              │
│  Extract user_id from claims                   │
│  Lookup user in database (fresh data)          │
│  │                                              │
│  ▼ (User found and active = Fully Trusted)    │
│  Inject User object into route                 │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│      Password Hashing Boundary                  │
│                                                 │
│  Untrusted: Plaintext password from client     │
│  │                                              │
│  ▼                                              │
│  PasslibUtils.hash_password()                  │
│  ├─ Never stored as plaintext                  │
│  ├─ Bcrypt algorithm (slow, salted)            │
│  ├─ Different hash for each call               │
│  │  (even for same password)                   │
│  │                                              │
│  ▼ (Hashed)                                     │
│  Stored in database                            │
│                                                 │
│  When verifying login:                         │
│  ├─ Get plaintext from client                  │
│  ├─ Get hash from database                     │
│  ├─ Bcrypt.verify(plaintext, hash)             │
│  │  (constant-time comparison)                 │
│  ├─ Never compare plaintext to plaintext       │
│  │                                              │
│  ▼ (Match = User authenticated)                │
│  Generate tokens                               │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│      Logging Boundary (Sensitive Data)          │
│                                                 │
│  Never log:                                     │
│  ✗ Passwords (plaintext or hashed)             │
│  ✗ Access tokens                               │
│  ✗ Refresh tokens                              │
│  ✗ Email addresses (unless necessary)          │
│  ✗ Phone numbers                               │
│  ✗ Credit card info                            │
│                                                 │
│  OK to log:                                     │
│  ✓ user_id (anonymized identifier)             │
│  ✓ Action performed (login, register)          │
│  ✓ Success/failure status                      │
│  ✓ Error codes (not messages)                  │
│  ✓ Request metadata (method, path, status)     │
│  ✓ Timestamps and request IDs                  │
│                                                 │
│  Logging filtered at logger level               │
│  Before data reaches log aggregation            │
│                                                 │
└─────────────────────────────────────────────────┘
```

This architecture diagram provides a comprehensive view of how all components interact, with emphasis on data flow, security boundaries, and operational deployment patterns.
