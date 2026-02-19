# Architecture & Design Documentation

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HTTP Client/Frontend                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    HTTP Request/Response
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    FastAPI Application                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Middleware Stack                          │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ 1. CORS Middleware                                  │  │   │
│  │  │    - Allow specific origins                         │  │   │
│  │  │    - Allow credentials                              │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ 2. Exception Handler Middleware                      │  │   │
│  │  │    - Catch all exceptions (highest level)           │  │   │
│  │  │    - Convert to error response                       │  │   │
│  │  │    - Log errors                                      │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ 3. Request Logging Middleware                        │  │   │
│  │  │    - Generate request ID (UUID)                      │  │   │
│  │  │    - Store in contextvars                            │  │   │
│  │  │    - Log request details                             │  │   │
│  │  │    - Calculate response time                         │  │   │
│  │  │    - Log response                                    │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └──────────────────────┬──────────────────────────────────────┘   │
│                         │                                          │
│  ┌──────────────────────▼──────────────────────────────────────┐   │
│  │         HTTP Routers & Route Handlers                       │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ /auth Router                                        │   │   │
│  │  │  POST /auth/register  → register()                  │   │   │
│  │  │  POST /auth/login     → login()                     │   │   │
│  │  │  POST /auth/refresh   → refresh_token()            │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ /health Router                                      │   │   │
│  │  │  GET  /health        → health_check()              │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ Auto-Generated Documentation                        │   │   │
│  │  │  GET  /docs          → Swagger UI                   │   │   │
│  │  │  GET  /redoc         → ReDoc                        │   │   │
│  │  │  GET  /openapi.json  → OpenAPI Schema              │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  └──────────────────────┬──────────────────────────────────────┘   │
│                         │                                          │
│  ┌──────────────────────▼──────────────────────────────────────┐   │
│  │    Dependency Injection Layer (FastAPI Depends)            │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ get_db_session()                                    │   │   │
│  │  │  - Provide AsyncSession for all routes              │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ get_current_user(token)                             │   │   │
│  │  │  - Extract token from Authorization header          │   │   │
│  │  │  - Verify JWT token                                 │   │   │
│  │  │  - Return User object                               │   │   │
│  │  │  - Raise 401 on invalid/expired token               │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ get_logger()                                        │   │   │
│  │  │  - Return configured logger instance                │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ get_request_id()                                    │   │   │
│  │  │  - Get request ID from contextvars                  │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  └──────────────────────┬──────────────────────────────────────┘   │
│                         │                                          │
│  ┌──────────────────────▼──────────────────────────────────────┐   │
│  │              Service Layer (Business Logic)                │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ AuthService                                        │   │   │
│  │  │  register_user(email, username, password)         │   │   │
│  │  │  login(email_or_username, password)               │   │   │
│  │  │  refresh_access_token(refresh_token)              │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ UserService                                        │   │   │
│  │  │  get_user_by_id(user_id)                          │   │   │
│  │  │  get_user_by_email(email)                         │   │   │
│  │  │  get_user_by_username(username)                   │   │   │
│  │  │  create_user(username, email, hashed_password)    │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  └──────────────────────┬──────────────────────────────────────┘   │
│                         │                                          │
│  ┌──────────────────────▼──────────────────────────────────────┐   │
│  │            Utility & Support Modules                       │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ app/utils/password.py                              │  │   │
│  │  │  hash_password(password)                           │  │   │
│  │  │  verify_password(password, hash)                   │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ app/utils/jwt.py                                   │  │   │
│  │  │  create_access_token(user_id)                      │  │   │
│  │  │  create_refresh_token(user_id)                     │  │   │
│  │  │  verify_token(token)                               │  │   │
│  │  │  extract_user_id_from_token(token)                 │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ app/utils/exceptions.py                            │  │   │
│  │  │  AppException (base)                               │  │   │
│  │  │  AuthException                                     │  │   │
│  │  │  InvalidCredentialsException                       │  │   │
│  │  │  UserAlreadyExistsException                        │  │   │
│  │  │  TokenExpiredException                             │  │   │
│  │  │  ValidationException                               │  │   │
│  │  │  DatabaseException                                 │  │   │
│  │  │  CircuitBreakerOpenException                       │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ app/utils/logger.py                                │  │   │
│  │  │  get_logger(name)                                  │  │   │
│  │  │  setup_logging(log_level)                          │  │   │
│  │  │  JSONFormatter (structured logging)                │  │   │
│  │  │  get_request_id()                                  │  │   │
│  │  │  set_request_id(request_id)                        │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ app/utils/circuit_breaker.py                       │  │   │
│  │  │  CircuitBreaker class                              │  │   │
│  │  │  States: CLOSED, OPEN, HALF_OPEN                   │  │   │
│  │  │  Transitions based on failures/timeouts            │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ app/models/                                         │  │   │
│  │  │  User (SQLAlchemy ORM model)                        │  │   │
│  │  │  UserRegister (Pydantic schema)                     │  │   │
│  │  │  UserLogin (Pydantic schema)                        │  │   │
│  │  │  TokenResponse (Pydantic schema)                    │  │   │
│  │  │  RefreshTokenRequest (Pydantic schema)             │  │   │
│  │  │  ErrorResponse (Pydantic schema)                    │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └──────────────────────┬──────────────────────────────────────┘   │
│                         │                                          │
│  ┌──────────────────────▼──────────────────────────────────────┐   │
│  │              Data Access Layer                             │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ SQLAlchemy AsyncSession                             │  │   │
│  │  │  - Async ORM operations                             │  │   │
│  │  │  - Transaction management                           │  │   │
│  │  │  - Connection pooling                               │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ Database Configuration                              │  │   │
│  │  │  - SQLite (development/testing)                     │  │   │
│  │  │  - PostgreSQL (production)                          │  │   │
│  │  │  - Connection pooling configured                    │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └──────────────────────┬──────────────────────────────────────┘   │
└─────────────────────────┴──────────────────────────────────────────┘
                          │
        ┌─────────────────┴──────────────────┐
        │                                    │
    ┌───▼────┐                         ┌─────▼──────┐
    │ SQLite │                         │ PostgreSQL │
    │ .db    │                         │ Production │
    └────────┘                         └────────────┘
```

---

## Request Flow Diagram

### User Registration Flow

```
Client                          FastAPI App                         Database
  │                                 │                                  │
  ├─ POST /auth/register ─────────>│                                  │
  │  {email, username, password}    │                                  │
  │                                 │                                  │
  │                                 ├─ Logging Middleware             │
  │                                 │  └─ Generate request ID         │
  │                                 │  └─ Log request                 │
  │                                 │                                  │
  │                                 ├─ Route Handler: register()      │
  │                                 │                                  │
  │                                 ├─ Dependency: get_db_session    │
  │                                 │                                  │
  │                                 ├─ AuthService.register_user()    │
  │                                 │  ├─ UserService.get_user_by_email
  │                                 │  │  └─ SELECT * FROM users     │
  │                                 │  │      WHERE email = ?   <─────┤
  │                                 │  │  <────────────────────────── │
  │                                 │  │                              │
  │                                 │  ├─ Check if exists             │
  │                                 │  │  └─ Raise UserAlreadyExists  │
  │                                 │  │      if duplicate            │
  │                                 │  │                              │
  │                                 │  ├─ Hash password (bcrypt)      │
  │                                 │  │                              │
  │                                 │  ├─ UserService.create_user()   │
  │                                 │  │  └─ INSERT INTO users  ─────>│
  │                                 │  │                              │
  │                                 │  │  <───────────────────────────│
  │                                 │  │  Get created user           │
  │                                 │  │                              │
  │                                 │  ├─ Generate tokens             │
  │                                 │  │  ├─ JWT access token         │
  │                                 │  │  └─ JWT refresh token        │
  │                                 │  │                              │
  │                                 │  └─ Return TokenResponse        │
  │                                 │                                  │
  │                                 ├─ Response 201 Created          │
  │                                 │                                  │
  │                                 ├─ Logging Middleware             │
  │                                 │  └─ Log response               │
  │                                 │                                  │
  │<─ 201 {access_token, ...} ────│                                  │
  │                                 │                                  │
```

### User Login Flow

```
Client                          FastAPI App                         Database
  │                                 │                                  │
  ├─ POST /auth/login ──────────────>│                                  │
  │  {email/username, password}      │                                  │
  │                                 │                                  │
  │                                 ├─ Logging Middleware             │
  │                                 │  └─ Generate request ID         │
  │                                 │                                  │
  │                                 ├─ Route Handler: login()         │
  │                                 │                                  │
  │                                 ├─ AuthService.login()            │
  │                                 │  ├─ UserService.get_user_by_email/username
  │                                 │  │  └─ SELECT * FROM users  ─>│
  │                                 │  │      WHERE email = ?        │
  │                                 │  │  <───────────────────────── │
  │                                 │  │                              │
  │                                 │  ├─ Check if found              │
  │                                 │  │  └─ Raise InvalidCredentials │
  │                                 │  │      if not found            │
  │                                 │  │                              │
  │                                 │  ├─ Check is_active             │
  │                                 │  │  └─ Raise InvalidCredentials │
  │                                 │  │      if inactive             │
  │                                 │  │                              │
  │                                 │  ├─ Verify password (bcrypt)    │
  │                                 │  │  └─ Raise InvalidCredentials │
  │                                 │  │      if wrong                │
  │                                 │  │                              │
  │                                 │  ├─ Update last_login           │
  │                                 │  │  └─ UPDATE users SET  ──────>│
  │                                 │  │      last_login = NOW        │
  │                                 │  │  <───────────────────────────│
  │                                 │  │                              │
  │                                 │  ├─ Generate tokens             │
  │                                 │  │  ├─ JWT access token         │
  │                                 │  │  └─ JWT refresh token        │
  │                                 │  │                              │
  │                                 │  └─ Return TokenResponse        │
  │                                 │                                  │
  │                                 ├─ Response 200 OK               │
  │                                 │                                  │
  │<─ 200 {access_token, ...} ────│                                  │
  │                                 │                                  │
```

### Protected Route Access Flow

```
Client                          FastAPI App                    Database
  │                                 │                               │
  ├─ GET /protected ──────────────>│                               │
  │  Authorization: Bearer <token>  │                               │
  │                                 │                               │
  │                                 ├─ Dependency: get_current_user│
  │                                 │  ├─ Extract token from header │
  │                                 │  ├─ JWT verify_token(token)   │
  │                                 │  │  └─ Validate signature     │
  │                                 │  │  └─ Check expiration       │
  │                                 │  │  └─ Raise TokenExpired    │
  │                                 │  │      if invalid/expired    │
  │                                 │  │                               │
  │                                 │  ├─ Extract user_id from token
  │                                 │  │                               │
  │                                 │  ├─ UserService.get_user_by_id │
  │                                 │  │  └─ SELECT * FROM users ──>│
  │                                 │  │      WHERE id = ?          │
  │                                 │  │  <──────────────────────── │
  │                                 │  │                               │
  │                                 │  ├─ Check is_active             │
  │                                 │  │  └─ Raise exception if    │
  │                                 │  │      inactive              │
  │                                 │  │                               │
  │                                 │  └─ Return User object         │
  │                                 │                               │
  │                                 ├─ Route Handler (has User)     │
  │                                 │  └─ Process request with User │
  │                                 │                               │
  │                                 ├─ Response 200 OK             │
  │                                 │                               │
  │<────── 200 {data} ────────────│                               │
  │                                 │                               │
```

---

## Exception Flow Diagram

```
Request
  │
  ├─> Route Handler
  │    │
  │    ├─> Service Layer
  │    │    │
  │    │    ├─ Data Access
  │    │    │  └─ Raise DatabaseException
  │    │    │
  │    │    ├─ Business Logic
  │    │    │  ├─ UserAlreadyExistsException
  │    │    │  ├─ InvalidCredentialsException
  │    │    │  └─ ValidationException
  │    │
  │    ├─ Dependency Injection
  │    │  ├─ TokenExpiredException
  │    │  └─ InvalidTokenException
  │
  ├─> Exception Handler Middleware
  │    │
  │    ├─ Catch all exceptions
  │    │
  │    ├─ Map to HTTP status code
  │    │  ├─ 400 for ValidationException
  │    │  ├─ 401 for TokenExpiredException
  │    │  ├─ 409 for UserAlreadyExistsException
  │    │  └─ 500 for unhandled exceptions
  │    │
  │    ├─ Log error with request ID
  │    │
  │    └─ Return error response
  │         {
  │           "detail": "Error message",
  │           "error_code": "ERROR_CODE",
  │           "timestamp": "2024-01-15T...",
  │           "request_id": "uuid..."
  │         }
  │
  └─> HTTP Response to Client
```

---

## State Machine Diagrams

### JWT Token Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    JWT Token Lifecycle                      │
└─────────────────────────────────────────────────────────────┘

Created (login/register)
       │
       ├─ [Access Token]
       │  ├─ Valid: 30 minutes
       │  ├─ Claim: {sub: user_id, exp: timestamp}
       │  └─ Used: Authorization: Bearer <token>
       │     │
       │     ├─ [VALID]
       │     │  └─ Allow request
       │     │
       │     ├─ [EXPIRED] (after 30 min)
       │     │  └─ Return 401 Unauthorized
       │     │
       │     └─ [INVALID]
       │        └─ Return 401 Unauthorized
       │
       ├─ [Refresh Token]
       │  ├─ Valid: 7 days
       │  ├─ Claim: {sub: user_id, exp: timestamp, type: refresh}
       │  └─ Used: POST /auth/refresh with refresh_token
       │     │
       │     ├─ [VALID]
       │     │  └─ Generate new access token
       │     │
       │     └─ [EXPIRED] (after 7 days)
       │        └─ Return 401 Unauthorized
       │        └─ User must login again
       │
       └─ [Both tokens can be used for login]
```

### Circuit Breaker State Machine

```
┌───────────────────────────────────────────────────────────────┐
│                  Circuit Breaker States                       │
└───────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │    CLOSED       │ ◄────────────────────┐
                    │ (Normal State)  │                      │
                    └────────┬────────┘                      │
                             │                              │
                    Allow all requests                      │
                             │                              │
                    ┌────────▼────────┐                     │
                    │   Request OK?   │                     │
                    └────────┬────────┘                     │
                       ┌─────┴─────┐                        │
                       │           │                        │
                      YES         NO                        │
                       │           │                        │
                    [Reset]    [Increment failure count]    │
                       │           │                        │
                       │    ┌──────▼──────┐                │
                       │    │ Threshold   │                │
                       │    │ reached?    │                │
                       │    └──────┬──────┘                │
                       │          NO                       │
                       │           │ YES                    │
                       │           │                       │
                       │    ┌──────▼──────┐               │
                       │    │    OPEN     │               │
                       │    │ (Failing)   │               │
                       │    └──────┬──────┘               │
                       │           │                       │
                       │    [Reject all requests]         │
                       │    [Start timeout timer]         │
                       │           │                       │
                       │    ┌──────▼──────┐               │
                       │    │  Timeout    │               │
                       │    │  expired?   │               │
                       │    └──────┬──────┘               │
                       │           │ YES                   │
                       │           │                       │
                       │    ┌──────▼──────┐               │
                       │    │ HALF-OPEN   │               │
                       │    │ (Testing)   │               │
                       │    └──────┬──────┘               │
                       │           │                       │
                       │    Allow ONE request             │
                       │           │                       │
                       │    ┌──────▼──────┐               │
                       │    │ Request OK? │               │
                       │    └──────┬──────┘               │
                       │      ┌────┴────┐                 │
                       │      │         │                 │
                       │     YES        NO                 │
                       │      │         │                 │
                       │      │    [Return to OPEN]       │
                       │      │         │                 │
                       └──────┘         └─────────────────┘
```

---

## Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      users Table                             │
├─────────────────────────────────────────────────────────────┤
│ Column          │ Type         │ Constraints              │
├─────────────────┼──────────────┼──────────────────────────┤
│ id              │ INTEGER      │ PRIMARY KEY, AUTOINCREMENT
│ username        │ VARCHAR(50)  │ UNIQUE NOT NULL, INDEX  │
│ email           │ VARCHAR(100) │ UNIQUE NOT NULL, INDEX  │
│ hashed_password │ VARCHAR(255) │ NOT NULL                │
│ is_active       │ BOOLEAN      │ DEFAULT TRUE            │
│ created_at      │ DATETIME     │ DEFAULT CURRENT_TIME    │
│ updated_at      │ DATETIME     │ DEFAULT CURRENT_TIME    │
│ last_login      │ DATETIME     │ NULLABLE                │
├─────────────────────────────────────────────────────────────┤
│ Indexes:                                                     │
│  - idx_users_username ON (username)                         │
│  - idx_users_email ON (email)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer Dependencies

```
┌──────────────────────────────────────────────────────────┐
│                  Dependency Hierarchy                    │
└──────────────────────────────────────────────────────────┘

Top Level:
  HTTP Clients → FastAPI Routes

Routes Layer:
  app/routes/auth.py
  app/routes/health.py
  │
  └─ Depends on: Services, Schemas, Dependencies

Dependencies:
  app/dependencies.py
  │
  └─ Depends on: JWT Utils, User Service, Logger

Service Layer:
  app/services/auth_service.py
  app/services/user_service.py
  │
  ├─ Depends on: Models, Database, Utils
  └─ Uses: Password, JWT, Exceptions, Logger

Utils Layer (No dependencies on services/routes):
  app/utils/password.py
  app/utils/jwt.py
  app/utils/exceptions.py
  app/utils/logger.py
  app/utils/circuit_breaker.py
  │
  └─ Depends only on: stdlib, third-party libs, config

Middleware Layer:
  app/middleware/exception.py
  app/middleware/logging.py
  │
  └─ Depends on: Exceptions, Logger

Data Layer:
  app/models/user.py (SQLAlchemy)
  app/models/schemas.py (Pydantic)
  app/database.py (SQLAlchemy async engine)
  │
  └─ Depends only on: stdlib, SQLAlchemy, Pydantic
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Production Setup                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Load Balancer (Nginx/HAProxy)              │
│  - HTTPS termination                                    │
│  - Health check: GET /health                            │
│  - Route to multiple app instances                      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼──┐    ┌────▼──┐    ┌────▼──┐
   │App #1 │    │App #2 │    │App #3 │
   │Port   │    │Port   │    │Port   │
   │8000   │    │8001   │    │8002   │
   └───┬───┘    └───┬───┘    └───┬───┘
       │            │            │
       └────────────┼────────────┘
                    │
         ┌──────────▼──────────┐
         │  PostgreSQL Database │
         │  - Connection Pool   │
         │  - Replicas (opt)    │
         │  - Backups           │
         └──────────────────────┘

Logging & Monitoring:
         ┌───────────────────────┐
         │ Structured Logs (JSON)│
         │ - Request ID          │
         │ - User ID             │
         │ - Status codes        │
         │ - Duration            │
         └────────────┬──────────┘
                      │
         ┌────────────▼──────────┐
         │ Log Aggregation       │
         │ (ELK/Splunk/etc)      │
         └───────────────────────┘

Monitoring & Alerts:
         ┌───────────────────────┐
         │ Metrics Collection    │
         │ - Request/sec         │
         │ - Error rate          │
         │ - Response time       │
         │ - DB pool usage       │
         └────────────┬──────────┘
                      │
         ┌────────────▼──────────┐
         │ Prometheus/Datadog    │
         │ Grafana Dashboards    │
         │ Alerts                │
         └───────────────────────┘
```

---

## Configuration Flow

```
Environment Variables (.env)
  │
  ├─ DATABASE_URL
  │  └─ SQLite: sqlite:///./test.db
  │  └─ PostgreSQL: postgresql+asyncpg://user:pass@host/db
  │
  ├─ JWT_SECRET_KEY (REQUIRED - no default)
  │
  ├─ JWT_ALGORITHM (default: HS256)
  │
  ├─ ACCESS_TOKEN_EXPIRE_MINUTES (default: 30)
  │
  ├─ REFRESH_TOKEN_EXPIRE_DAYS (default: 7)
  │
  ├─ ENVIRONMENT (default: development)
  │  └─ development | staging | production
  │
  ├─ LOG_LEVEL (default: INFO)
  │  └─ DEBUG | INFO | WARNING | ERROR | CRITICAL
  │
  ├─ DATABASE_MAX_POOL_SIZE (default: 20)
  │
  ├─ CIRCUIT_BREAKER_THRESHOLD (default: 5)
  │
  ├─ CIRCUIT_BREAKER_TIMEOUT (default: 60)
  │
  └─ CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS (default: 1)

Loaded by:
  app/config.py → Settings (pydantic-settings)
                  ├─ Reads from .env file
                  ├─ Reads from environment variables
                  └─ Uses defaults as fallback

Used by:
  ├─ app/main.py → FastAPI app config
  ├─ app/database.py → DB connection string
  ├─ app/utils/jwt.py → JWT settings
  ├─ app/utils/logger.py → Log level
  └─ app/middleware → Logging/exception config
```

---

## API Contract Documentation

### Request/Response Examples

#### Registration Request/Response
```
POST /auth/register

Request:
{
  "email": "user@example.com",
  "username": "newuser",
  "password": "SecurePassword123!"
}

Response (201 Created):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "newuser",
    "is_active": true,
    "created_at": "2024-01-15T10:30:45.123Z",
    "last_login": null
  }
}

Error Response (400 Bad Request):
{
  "detail": "Email already registered",
  "error_code": "USER_ALREADY_EXISTS",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Login Request/Response
```
POST /auth/login

Request:
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "newuser",
    "is_active": true,
    "created_at": "2024-01-15T10:30:45.123Z",
    "last_login": "2024-01-15T10:35:20.456Z"
  }
}

Error Response (401 Unauthorized):
{
  "detail": "Invalid credentials",
  "error_code": "INVALID_CREDENTIALS",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Token Refresh Request/Response
```
POST /auth/refresh

Request:
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { ... }
}

Error Response (401 Unauthorized):
{
  "detail": "Invalid or expired token",
  "error_code": "TOKEN_EXPIRED",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Health Check Request/Response
```
GET /health

Response (200 OK):
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

---

## Summary

This architecture document provides:
1. **System architecture diagram** showing all layers and components
2. **Request flow diagrams** for key operations
3. **Exception flow** showing error handling path
4. **State machines** for JWT tokens and circuit breaker
5. **Database schema** with tables and indexes
6. **Dependency hierarchy** showing what depends on what
7. **Deployment architecture** for production setup
8. **Configuration flow** showing environment variables
9. **API contract examples** for all endpoints

This comprehensive view helps understand how all components interact and integrate into a cohesive system.
