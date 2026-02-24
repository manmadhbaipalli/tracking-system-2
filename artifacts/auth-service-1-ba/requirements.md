# Requirements: auth-service-1

## Overview

A Python FastAPI application providing user authentication services — specifically user registration and login endpoints. The system manages user accounts with email/password credentials, issues JWT tokens on successful authentication, and enforces role-based access control. It serves end users (registering and logging in) and administrators (managing users).

---

## User Stories

### US-001: User Registration
**As a** new user
**I want to** register with my email and password
**So that** I can create an account and access the system
**Priority:** High
**Story Points:** 5

**Acceptance Criteria:**
- AC-001.1: System accepts `email`, `password`, and `name` fields in the request body
- AC-001.2: System validates that `email` is a valid email format
- AC-001.3: System validates that `email` is unique (not already registered)
- AC-001.4: System validates that `password` is at least 8 characters long
- AC-001.5: System validates that `name` is non-empty and at most 100 characters
- AC-001.6: System stores the password as a BCrypt hash — never plain text
- AC-001.7: System returns HTTP 201 Created with a JWT access token and user profile (id, email, name, role) on success
- AC-001.8: System assigns the default role of `USER` to newly registered accounts

**Error Scenarios:**
- E-001.1: Duplicate email → 409 Conflict with message `"Email already registered"`
- E-001.2: Invalid email format → 400 Bad Request with field error on `email`
- E-001.3: Password shorter than 8 characters → 400 Bad Request with field error on `password`
- E-001.4: Missing required field → 400 Bad Request with field error listing missing fields
- E-001.5: Name exceeds 100 characters → 400 Bad Request with field error on `name`

---

### US-002: User Login
**As a** registered user
**I want to** log in with my email and password
**So that** I can obtain a JWT token to authenticate subsequent requests
**Priority:** High
**Story Points:** 5

**Acceptance Criteria:**
- AC-002.1: System accepts `email` and `password` in the request body
- AC-002.2: System verifies the provided password against the stored BCrypt hash
- AC-002.3: System returns HTTP 200 OK with a JWT access token and user profile (id, email, name, role) on successful login
- AC-002.4: JWT token includes `sub` (user id), `email`, `role`, `iat` (issued at), and `exp` (expiration) claims
- AC-002.5: JWT token expiration is configurable via environment variable (default: 30 minutes)
- AC-002.6: System rejects login for deactivated (soft-deleted) users

**Error Scenarios:**
- E-002.1: Email not found → 401 Unauthorized with message `"Invalid credentials"`
- E-002.2: Password does not match → 401 Unauthorized with message `"Invalid credentials"` (same message as E-002.1 to prevent user enumeration)
- E-002.3: Missing required field → 400 Bad Request with field error listing missing fields
- E-002.4: Account deactivated → 401 Unauthorized with message `"Account is deactivated"`

---

### US-003: Get Current User Profile
**As an** authenticated user
**I want to** retrieve my own profile
**So that** I can view my account details
**Priority:** Medium
**Story Points:** 3

**Acceptance Criteria:**
- AC-003.1: Endpoint requires a valid Bearer JWT token in the `Authorization` header
- AC-003.2: System returns HTTP 200 OK with the authenticated user's profile (id, email, name, role, active, created_at)
- AC-003.3: System does not return the password hash in the response

**Error Scenarios:**
- E-003.1: Missing or malformed Authorization header → 401 Unauthorized with message `"Not authenticated"`
- E-003.2: Expired JWT token → 401 Unauthorized with message `"Token has expired"`
- E-003.3: Invalid/tampered JWT token → 401 Unauthorized with message `"Invalid token"`

---

### US-004: Update Current User Profile
**As an** authenticated user
**I want to** update my name or password
**So that** I can keep my account information current
**Priority:** Medium
**Story Points:** 5

**Acceptance Criteria:**
- AC-004.1: Endpoint requires a valid Bearer JWT token
- AC-004.2: System accepts optional `name` and/or `password` fields; at least one must be provided
- AC-004.3: If `password` is updated, the new value must be at least 8 characters and stored as a BCrypt hash
- AC-004.4: System returns HTTP 200 OK with the updated user profile on success
- AC-004.5: User cannot change their own `email` or `role` via this endpoint

**Error Scenarios:**
- E-004.1: No fields provided → 400 Bad Request with message `"At least one field must be provided"`
- E-004.2: New password too short → 400 Bad Request with field error on `password`
- E-004.3: Unauthenticated request → 401 Unauthorized
- E-004.4: Name exceeds 100 characters → 400 Bad Request with field error on `name`

---

### US-005: Admin — List All Users
**As an** administrator
**I want to** list all registered users with pagination
**So that** I can manage the user base
**Priority:** Medium
**Story Points:** 3

**Acceptance Criteria:**
- AC-005.1: Endpoint is accessible only to users with the `ADMIN` role
- AC-005.2: System returns a paginated list of users with fields: id, email, name, role, active, created_at
- AC-005.3: Pagination is controlled via `page` (default: 1) and `page_size` (default: 20, max: 100) query parameters
- AC-005.4: Response includes total count, page, page_size, and items
- AC-005.5: System does not return password hashes in the response

**Error Scenarios:**
- E-005.1: Non-admin user → 403 Forbidden with message `"Insufficient permissions"`
- E-005.2: Unauthenticated request → 401 Unauthorized
- E-005.3: `page_size` exceeds 100 → 400 Bad Request

---

### US-006: Admin — Deactivate/Reactivate User
**As an** administrator
**I want to** deactivate or reactivate a user account
**So that** I can control access without permanently deleting accounts
**Priority:** Medium
**Story Points:** 3

**Acceptance Criteria:**
- AC-006.1: Endpoint is accessible only to users with the `ADMIN` role
- AC-006.2: System sets `active = false` on deactivation and `active = true` on reactivation
- AC-006.3: System returns HTTP 200 OK with the updated user profile
- AC-006.4: Admin cannot deactivate their own account

**Error Scenarios:**
- E-006.1: User not found → 404 Not Found with message `"User not found"`
- E-006.2: Non-admin user → 403 Forbidden
- E-006.3: Admin attempting to deactivate own account → 400 Bad Request with message `"Cannot deactivate your own account"`

---

### US-007: Admin — Update User Role
**As an** administrator
**I want to** promote or demote a user's role
**So that** I can control administrative access
**Priority:** Low
**Story Points:** 3

**Acceptance Criteria:**
- AC-007.1: Endpoint is accessible only to users with the `ADMIN` role
- AC-007.2: System accepts `role` field with value `USER` or `ADMIN`
- AC-007.3: System returns HTTP 200 OK with the updated user profile
- AC-007.4: Admin cannot change their own role

**Error Scenarios:**
- E-007.1: User not found → 404 Not Found
- E-007.2: Invalid role value → 400 Bad Request with field error on `role`
- E-007.3: Admin attempting to change own role → 400 Bad Request with message `"Cannot change your own role"`
- E-007.4: Non-admin user → 403 Forbidden

---

### US-008: Health Check
**As a** platform operator
**I want to** query liveness and readiness endpoints
**So that** I can monitor the service and integrate it with orchestration systems
**Priority:** High
**Story Points:** 2

**Acceptance Criteria:**
- AC-008.1: `GET /health/liveness` returns 200 OK with `{"status": "ok"}` when the process is running
- AC-008.2: `GET /health/readiness` returns 200 OK with `{"status": "ok", "database": "ok"}` when the database is reachable
- AC-008.3: `GET /health/readiness` returns 503 Service Unavailable with `{"status": "error", "database": "unreachable"}` when the database is not reachable

**Error Scenarios:**
- E-008.1: Database unreachable at readiness check → 503 with database status detail

---

## Business Rules

- **BR-001: Email Uniqueness** — No two active users can share the same email address. Uniqueness is enforced at the database level (unique index) and application level.
- **BR-002: Password Hashing** — Passwords MUST be stored as BCrypt hashes. Plain-text passwords must never be stored, logged, or returned in any API response.
- **BR-003: Default Role** — Newly registered users receive the `USER` role. The `ADMIN` role can only be assigned by an existing admin via the role-update endpoint.
- **BR-004: Soft Delete** — Users are never physically deleted. Deactivated users have `active = false` and are blocked from logging in.
- **BR-005: Audit Timestamps** — Every `User` entity records `created_at` (immutable, set at creation) and `updated_at` (updated on every change).
- **BR-006: Credential Error Uniformity** — Login errors for unknown email and wrong password MUST return the same error message (`"Invalid credentials"`) to prevent user enumeration.
- **BR-007: JWT Secret Confidentiality** — The JWT signing secret must be supplied via environment variable and must never be hardcoded in source files.
- **BR-008: Password in Responses** — The `password_hash` field must never appear in any API response, regardless of endpoint.
- **BR-009: Self-Protection** — Admins cannot deactivate their own account or change their own role to prevent accidental lockout.
- **BR-010: Token Stateless** — Authentication is stateless; the server does not maintain a session store. Token validity is determined solely by JWT signature and expiration.

---

## Non-Functional Requirements

### Performance
- API response time: < 500ms at 95th percentile under normal load
- Database queries: < 100ms for simple single-record lookups
- BCrypt work factor: configurable (default: 12); must balance security and latency (< 1 second per hash operation)
- Pagination: default 20 items per page, max 100 items per page on list endpoints

### Security
- Authentication: JWT (HS256 or RS256) with configurable expiration (default 30 minutes)
- Authorization: Role-Based Access Control (RBAC) with roles `USER` and `ADMIN`
- Password storage: BCrypt — never plain text
- Input validation: All request bodies validated with strict schemas; unknown fields rejected or ignored
- CORS: Configurable allowed origins via environment variable; wildcard (`*`) must not be used in production
- Sensitive data: Passwords, hashes, and raw JWT secrets must never appear in logs
- HTTP security headers: Recommended headers (e.g., `X-Content-Type-Options`, `X-Frame-Options`) applied

### Reliability
- Liveness and readiness health check endpoints
- Graceful error handling — no Python stack traces exposed in API responses
- Database connection pooling (configurable pool size)
- Application startup validates required environment variables and fails fast with a clear error message if any are missing

### Observability
- Structured JSON logging (level, timestamp, correlation_id, message, path, method, status_code)
- Each incoming request is assigned a unique `correlation_id` (UUID) propagated through log entries
- Request and response logged (excluding request body fields: `password`, `password_hash`)
- Log level configurable via environment variable (default: `INFO`)

### Scalability
- Stateless authentication (JWT) — no server-side session storage; horizontally scalable
- All list endpoints paginated to prevent unbounded queries
- Database connection pooling to support concurrent requests

### Configuration
- All configuration via environment variables (no hardcoded values):
  - `DATABASE_URL` — database connection string
  - `SECRET_KEY` — JWT signing secret
  - `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT expiration (default: 30)
  - `BCRYPT_ROUNDS` — BCrypt work factor (default: 12)
  - `CORS_ORIGINS` — comma-separated list of allowed origins
  - `LOG_LEVEL` — logging level (default: INFO)
- Application fails fast on startup if `DATABASE_URL` or `SECRET_KEY` are missing

---

## Domain Model

### User

| Attribute | Type | Constraints | Default |
|-----------|------|-------------|---------|
| id | integer | PK, auto-generated | — |
| email | string(255) | unique, not null, indexed | — |
| password_hash | string(255) | not null | — |
| name | string(100) | not null | — |
| role | enum [USER, ADMIN] | not null | USER |
| active | boolean | not null | true |
| created_at | datetime (UTC) | not null, immutable, set at insert | now() |
| updated_at | datetime (UTC) | not null, updated on every change | now() |

**Relationships:**
- No foreign key relationships in initial scope; `User` is the sole domain entity.

**Indexes:**
- `users.email` — unique index (enforces BR-001)

**State Machine — User.active:**
```
ACTIVE (active=true) --[Admin deactivates]--> INACTIVE (active=false)
INACTIVE             --[Admin reactivates]--> ACTIVE (active=true)
INACTIVE             --[Login attempt]-------> 401 Unauthorized
```

---

## Integration Requirements

### Database
- **Trigger:** All CRUD operations on `User`
- **Data sent:** SQL queries via ORM (SQLAlchemy or equivalent)
- **Data received:** Query results / row counts
- **Error handling:** Database errors return 500 Internal Server Error with a generic message (no SQL details exposed to client); errors are logged internally

### No External Integrations (Initial Scope)
- Email service (password reset, welcome email): **Out of scope** — noted as open question
- OAuth/SSO providers: **Out of scope**
- Token revocation / blocklist: **Out of scope** (see BR-010)

---

## Traceability Matrix

| Requirement | Feature ID | Priority | Story Points | Agent |
|-------------|-----------|----------|--------------|-------|
| US-001 User Registration | auth-register | High | 5 | dev |
| US-002 User Login | auth-login | High | 5 | dev |
| US-003 Get Current User Profile | user-profile-get | Medium | 3 | dev |
| US-004 Update Current User Profile | user-profile-update | Medium | 5 | dev |
| US-005 Admin List Users | user-management-list | Medium | 3 | dev |
| US-006 Admin Deactivate/Reactivate User | user-management-status | Medium | 3 | dev |
| US-007 Admin Update User Role | user-management-role | Low | 3 | dev |
| US-008 Health Check | health-check | High | 2 | dev |
| BR-001 Email Uniqueness | auth-register | High | — | dba |
| BR-002 Password Hashing | auth-register, auth-login | High | — | dev |
| BR-003 Default Role | auth-register | High | — | dev |
| BR-004 Soft Delete | user-management-status | Medium | — | dba |
| BR-005 Audit Timestamps | base-entity-audit | High | 2 | dev |
| BR-006 Credential Error Uniformity | auth-login | High | — | dev |
| BR-007 JWT Secret Config | jwt-auth | High | — | dev |
| BR-009 Self-Protection | user-management-status, user-management-role | Medium | — | dev |
| NFR-Security | jwt-auth, bcrypt | High | 8 | dev |
| NFR-Observability | structured-logging, health-check | Medium | 3 | dev |
| NFR-Configuration | env-config | High | 2 | dev |
| NFR-Reliability | error-handling, health-check | High | 3 | dev |

**Total Story Points:** 55

---

## Open Questions

1. **Password Reset Flow** — Should the system support a "Forgot Password" / password reset via email? This would require an email integration. Currently out of scope but may be a future requirement.
2. **Email Verification** — Should new registrations require email verification before the account is active? Currently not required in the task description.
3. **Token Refresh** — Should the system support refresh tokens (long-lived) in addition to access tokens (short-lived)? Not specified — currently only access tokens are scoped.
4. **Relational Database** — Which database engine is preferred (PostgreSQL, MySQL, SQLite)? The architecture agent will decide, but this affects migration tooling choices.
5. **API Versioning** — Should endpoints be versioned (e.g., `/api/v1/auth/register`)? Not specified; assumed yes for production readiness.
6. **Rate Limiting** — Should login and registration endpoints implement rate limiting to prevent brute-force attacks? Recommended but not explicitly requested.
7. **Deployment Target** — Is the service containerized (Docker)? Affects configuration and health check endpoint paths. Assumed Docker for production.
