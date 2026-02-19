# Auth Service Architecture & Design

## 1. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Browser                          │
└─────────────────────────────────────────────────────────────────┘
                                  │
                         HTTP/HTTPS Requests
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Middleware Layer (Request In)                  │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  1. RequestID Generation (UUID)                           │   │
│  │  2. Logging Middleware (Request/Response logging)         │   │
│  │  3. CORS Middleware (Origin validation)                   │   │
│  │  4. Rate Limiting Middleware (Auth endpoints)             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Router Layer (Route Matching)                │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  POST /auth/register     → register_user()               │   │
│  │  POST /auth/login        → login_user()                  │   │
│  │  POST /auth/refresh      → refresh_token()               │   │
│  │  GET  /health            → health_check()                │   │
│  │  GET  /docs              → Swagger UI (auto-generated)    │   │
│  │  GET  /redoc             → ReDoc (auto-generated)         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Dependency Injection Layer                        │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  get_current_user(token) → Validates JWT, Returns User   │   │
│  │  get_db_session()        → Provides Database Session      │   │
│  │  get_logger()            → Returns Logger with RequestID  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Service Layer (Business Logic)                │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  AuthService                                       │  │   │
│  │  │  ├─ register_user(username, email, password)     │  │   │
│  │  │  ├─ login(email_or_username, password)           │  │   │
│  │  │  └─ refresh_access_token(refresh_token)          │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  UserService                                       │  │   │
│  │  │  ├─ get_user_by_id(user_id)                       │  │   │
│  │  │  ├─ get_user_by_email(email)                      │  │   │
│  │  │  ├─ get_user_by_username(username)                │  │   │
│  │  │  └─ create_user(username, email, hashed_password) │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Utility/Infrastructure Layer                   │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐│   │
│  │  │  JWT Utils   │  │ Password     │  │  Circuit        ││   │
│  │  │              │  │ Hashing      │  │  Breaker        ││   │
│  │  │ create_token │  │              │  │                 ││   │
│  │  │ verify_token │  │ hash_pwd     │  │ Closed/Open/    ││   │
│  │  │              │  │ verify_pwd   │  │ Half-Open       ││   │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘│   │
│  │                                                            │   │
│  │  ┌──────────────┐  ┌──────────────────────────────────┐  │   │
│  │  │  Logger      │  │  Custom Exceptions               │  │   │
│  │  │              │  │                                   │  │   │
│  │  │ Structured   │  │ - AuthException                  │  │   │
│  │  │ JSON output  │  │ - ValidationException            │  │   │
│  │  │ with RequestID  │ - UserAlreadyExistsException     │  │   │
│  │  │              │  │ - InvalidCredentialsException    │  │   │
│  │  │              │  │ - TokenExpiredException          │  │   │
│  │  └──────────────┘  └──────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Exception Handling Middleware               │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Catches all exceptions and returns:                      │   │
│  │  {                                                         │   │
│  │    "detail": "Error message",                            │   │
│  │    "error_code": "AUTH_001",                             │   │
│  │    "request_id": "550e8400-e29b-41d4-a716-446655440000" │   │
│  │  }                                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
└──────────────────────────│────────────────────────────────────────┘
                           │
                      Middleware Layer
                      (Response Out)
                           │
                    HTTP Response
                           │
┌──────────────────────────────────────────────────────────────────┐
│                         Database Layer                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           SQLAlchemy Async ORM                           │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  User Model                                              │   │
│  │  ├─ id (int, primary key)                               │   │
│  │  ├─ username (str, unique)                              │   │
│  │  ├─ email (str, unique)                                 │   │
│  │  ├─ hashed_password (str)                               │   │
│  │  ├─ is_active (bool)                                    │   │
│  │  ├─ created_at (datetime)                               │   │
│  │  ├─ updated_at (datetime)                               │   │
│  │  └─ last_login (datetime, nullable)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
└──────────────────────────│────────────────────────────────────────┘
                           │
                    Async Engine
                    (SQLite/PostgreSQL)
                           │
┌──────────────────────────────────────────────────────────────────┐
│                       Database Storage                            │
│                  (SQLite or PostgreSQL)                           │
└──────────────────────────────────────────────────────────────────┘
```

## 2. Request Flow Diagrams

### 2.1 User Registration Flow

```
Client: POST /auth/register
    {
        "email": "user@example.com",
        "username": "john_doe",
        "password": "secure_password"
    }
            │
            ▼
RequestID Middleware: Generate UUID for request
            │
            ▼
Logging Middleware: Log incoming request
            │
            ▼
Validation (Pydantic):
    - Valid email format?
    - Username length valid?
    - Password meets requirements?
            │
            ▼
Register Route Handler
            │
            ▼
AuthService.register_user()
    │
    ├─ UserService.get_user_by_email() → Check if exists
    │
    ├─ UserService.get_user_by_username() → Check if exists
    │
    ├─ PasswordUtils.hash_password() → Generate bcrypt hash
    │
    └─ UserService.create_user() → Insert into database
            │
            ▼
Return UserResponse + Tokens
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": "user@example.com",
            "username": "john_doe",
            "is_active": true,
            "created_at": "2024-02-19T10:30:00Z",
            "last_login": null
        }
    }
            │
            ▼
Logging Middleware: Log response
            │
            ▼
Client Receives 201 Created
```

### 2.2 User Login Flow

```
Client: POST /auth/login
    {
        "email": "user@example.com",
        "password": "secure_password"
    }
            │
            ▼
RequestID Middleware: Generate UUID
            │
            ▼
Logging Middleware: Log request (without password)
            │
            ▼
Validation: Email or username + password provided
            │
            ▼
Login Route Handler
            │
            ▼
AuthService.login()
    │
    ├─ UserService.get_user_by_email() or get_user_by_username()
    │
    ├─ PasswordUtils.verify_password()
    │   └─ If invalid → raise InvalidCredentialsException
    │
    ├─ JWTUtils.create_access_token()
    │
    ├─ JWTUtils.create_refresh_token()
    │
    └─ Update User.last_login timestamp
            │
            ▼
Return TokenResponse with tokens
            │
            ▼
Client Receives 200 OK
```

### 2.3 Token Refresh Flow

```
Client: POST /auth/refresh
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
            │
            ▼
Validation: refresh_token provided
            │
            ▼
Refresh Route Handler
            │
            ▼
AuthService.refresh_access_token()
    │
    ├─ JWTUtils.verify_token(refresh_token)
    │   └─ If expired → raise TokenExpiredException
    │
    ├─ Extract user_id from token
    │
    ├─ UserService.get_user_by_id()
    │
    ├─ JWTUtils.create_access_token()
    │
    └─ JWTUtils.create_refresh_token()
            │
            ▼
Return new TokenResponse
            │
            ▼
Client Receives 200 OK
```

### 2.4 Protected Route Access Flow

```
Client: GET /protected-endpoint
    Headers: {
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
            │
            ▼
RequestID Middleware: Generate UUID
            │
            ▼
Route Handler with get_current_user() dependency
            │
            ▼
get_current_user() dependency:
    │
    ├─ Extract token from "Authorization: Bearer ..." header
    │
    ├─ JWTUtils.verify_token()
    │   └─ If invalid → raise 401 Unauthorized
    │
    ├─ Extract user_id from token payload
    │
    ├─ UserService.get_user_by_id()
    │
    ├─ Check user.is_active
    │   └─ If not active → raise 403 Forbidden
    │
    └─ Return User object to route
            │
            ▼
Route Handler executes with user context
            │
            ▼
Return response
            │
            ▼
Client Receives 200 OK
```

## 3. Exception Handling Flow

```
Any Layer (Route/Service/Middleware)
            │
            ▼
Raises Exception
            │
    ┌───────┴────────┬──────────────┬──────────────┬───────────┐
    │                │              │              │           │
    ▼                ▼              ▼              ▼           ▼
AuthException   ValidationException   UserAlready   InvalidCred   TokenExpired
(401)           (400)                 Exists(409)    entials(401) (401)
    │                │                  │             │           │
    └────────────────┴──────────────────┴─────────────┴───────────┘
                     │
                     ▼
    Exception Handler Middleware
                     │
    ┌────────────────┴────────────────┐
    │                                  │
    ▼                                  ▼
Get HTTP Status Code        Format Error Response
    │                                  │
    └────────────────┬────────────────┘
                     │
                     ▼
        Return JSON Error Response
        {
            "detail": "Invalid credentials",
            "error_code": "INVALID_CREDENTIALS",
            "request_id": "550e8400-e29b-41d4-a716-446655440000"
        }
                     │
                     ▼
           Client Receives Error
```

## 4. Logging Architecture

```
Application Layers
    │
    ├─ Routes (endpoint calls)
    │   └─ logger.info("POST /auth/register", extra={...})
    │
    ├─ Services (business logic)
    │   └─ logger.info("User registered", extra={...})
    │
    ├─ Utilities (helpers)
    │   └─ logger.debug("Password hashed", extra={...})
    │
    └─ Middleware
        └─ logger.info("Request received", extra={request_id, ...})
            │
            ▼
    Logger (app/utils/logger.py)
    Configured with:
    - Level: DEBUG/INFO/WARNING/ERROR/CRITICAL
    - Format: JSON (structured logging)
    - Handler: Console/File
    - Context: RequestID, User, Timestamp
            │
            ▼
    Context Variables:
    - request_id: UUID for request tracing
    - user_id: Current authenticated user
    - timestamp: ISO 8601 format
    - path: Request path
    - method: HTTP method
    - status_code: HTTP status
            │
            ▼
    Output (JSON)
    {
        "timestamp": "2024-02-19T10:30:00Z",
        "level": "INFO",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": 42,
        "path": "/auth/register",
        "method": "POST",
        "message": "User registered successfully",
        "username": "john_doe"
    }
            │
            ▼
    Logging System (Console/File/External Service)
```

## 5. Circuit Breaker State Machine

```
CLOSED State (Normal Operation)
    │
    ├─ All requests pass through
    ├─ Failures are counted
    │
    └─ If failures >= THRESHOLD (default: 5)
        │
        ▼
    OPEN State (Fail Fast)
        │
        ├─ All requests immediately rejected
        ├─ Raises CircuitBreakerOpenException
        ├─ Wait for TIMEOUT (default: 60 seconds)
        │
        └─ After TIMEOUT expires
            │
            ▼
        HALF_OPEN State (Testing Recovery)
            │
            ├─ Allow LIMITED requests (default: 1)
            ├─ Test if service recovered
            │
            ├─ If request succeeds → Return to CLOSED
            │
            └─ If request fails → Return to OPEN
                (reset timeout)
```

## 6. Database Schema Diagram

```
┌─────────────────────────────────────────────────────┐
│                    users table                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  id (Integer)                 [PRIMARY KEY]         │
│      AUTO_INCREMENT                                 │
│                                                     │
│  username (String, 50)        [UNIQUE, INDEX]       │
│      Example: "john_doe"                            │
│                                                     │
│  email (String, 100)          [UNIQUE, INDEX]       │
│      Example: "john@example.com"                    │
│                                                     │
│  hashed_password (String, 255)                      │
│      Example: "$2b$12$...bcrypt hash..."            │
│                                                     │
│  is_active (Boolean)          [DEFAULT: TRUE]       │
│      Track user status (active/inactive)            │
│                                                     │
│  created_at (DateTime)        [DEFAULT: NOW()]      │
│      Example: 2024-02-19 10:30:00                   │
│                                                     │
│  updated_at (DateTime)        [DEFAULT: NOW()]      │
│      Updated on record change                       │
│                                                     │
│  last_login (DateTime)        [NULLABLE]            │
│      Track user activity                            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 7. Dependency Graph

```
main.py (Entry Point)
    ├── config.py (Settings)
    ├── database.py (ORM Setup)
    │   └── models/user.py (User Model)
    ├── middleware/
    │   ├── logging.py
    │   │   └── utils/logger.py
    │   └── exception.py
    │       └── utils/exceptions.py
    ├── routes/
    │   ├── auth.py
    │   │   ├── services/auth_service.py
    │   │   ├── services/user_service.py
    │   │   ├── models/schemas.py
    │   │   └── dependencies.py
    │   └── health.py
    ├── services/
    │   ├── auth_service.py
    │   │   ├── utils/jwt.py
    │   │   ├── utils/password.py
    │   │   ├── utils/logger.py
    │   │   ├── utils/exceptions.py
    │   │   └── services/user_service.py
    │   └── user_service.py
    │       └── database.py
    ├── dependencies.py
    │   ├── utils/jwt.py
    │   ├── services/user_service.py
    │   ├── utils/logger.py
    │   └── utils/exceptions.py
    └── utils/
        ├── jwt.py
        │   ├── config.py
        │   └── utils/exceptions.py
        ├── password.py
        ├── circuit_breaker.py
        │   └── utils/exceptions.py
        ├── logger.py
        │   └── config.py
        └── exceptions.py
```

## 8. File Creation Order

### Phase 1: Foundation (must be created first)
```
1. app/utils/exceptions.py
   └─ Used by all other modules

2. app/utils/logger.py
   └─ Used by all other modules

3. app/dependencies.py
   └─ Used by routes

4. app/middleware/exception.py
   └─ Uses exceptions.py

5. app/middleware/logging.py
   └─ Uses logger.py

6. app/main.py
   └─ Assembles everything
```

### Phase 2: Services (before routes)
```
7. app/utils/password.py
   └─ Standalone utility

8. app/utils/jwt.py
   └─ Uses exceptions, config

9. app/services/user_service.py
   └─ Uses database, models

10. app/services/auth_service.py
    └─ Uses user_service, password, jwt, logger, exceptions
```

### Phase 3: Routes (uses services)
```
11. app/routes/auth.py
    └─ Uses all services and dependencies

12. app/routes/health.py
    └─ Simple health check
```

### Phase 4: Optional
```
13. app/utils/circuit_breaker.py
    └─ Resilience pattern
```

### Phase 5: Testing
```
14. tests/ (entire test suite)
    └─ Uses all above modules
```
