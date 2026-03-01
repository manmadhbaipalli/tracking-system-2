# Architecture: Integrated Policy, Claims, and Payments Platform

## Overview

This document describes the architecture of the Integrated Policy, Claims, and Payments Platform, a comprehensive insurance management system built with Python and FastAPI.

## Technology Stack

- **Backend Framework**: FastAPI (Python 3.11+)
- **Database**: SQLAlchemy (async) with SQLite (dev) and PostgreSQL (production)
- **Authentication**: JWT with Bearer tokens
- **Password Hashing**: Bcrypt via Passlib
- **Data Encryption**: Fernet (symmetric encryption)
- **Validation**: Pydantic v2
- **ASGI Server**: Uvicorn

## Architectural Patterns

### Layered Architecture

The application follows a strict layered architecture:

```
┌─────────────────────────────────────┐
│         API Layer (Routers)         │  ← HTTP requests/responses
├─────────────────────────────────────┤
│       Service Layer (Services)      │  ← Business logic
├─────────────────────────────────────┤
│    Data Access Layer (SQLAlchemy)   │  ← Database operations
├─────────────────────────────────────┤
│         Database (SQLite/PG)        │  ← Data storage
└─────────────────────────────────────┘
```

### Key Design Patterns

1. **Service Layer Pattern**: All business logic is encapsulated in service modules
2. **Repository Pattern**: SQLAlchemy ORM serves as the data access abstraction
3. **DTO Pattern**: Pydantic schemas separate internal models from API contracts
4. **Dependency Injection**: FastAPI's `Depends()` manages dependencies
5. **Factory Pattern**: Used for complex object creation (e.g., JWT tokens, encrypted data)

## Domain Model

### Core Entities

#### 1. User
- Manages system users with roles (admin, adjuster, agent)
- Authenticated via JWT tokens
- Password stored as bcrypt hash

#### 2. Policy
- Insurance policies with insured party details
- Vehicle and location information
- Coverage types, limits, and deductibles
- SSN/TIN encrypted at rest, masked in responses

#### 3. Claim
- Claims linked to policies
- Supports claim-level policy data for unverified policies
- Subrogation referral tracking
- Scheduled payment management
- Injury incident details and coding information

#### 4. Payment
- Payments linked to claims and policies
- Multiple payment methods: ACH, wire, card, Stripe, global payouts
- Full lifecycle: pending → approved → issued → void/reversed
- Reserve line allocation
- Tax reporting support

#### 5. PaymentDetail
- Multiple payees per payment
- Payment portions and deductions
- Encrypted banking information

#### 6. Vendor
- Vendor/provider onboarding
- Secure payment method storage
- KYC/identity verification support

#### 7. AuditLog
- Immutable audit trail
- Tracks all actions with user ID and timestamp
- Change tracking with old/new values

#### 8. Document
- Attachment support for policies, claims, and payments
- File metadata tracking

## Entity Relationships

```
User ─────┬─ creates ───→ Policy
          ├─ creates ───→ Claim
          └─ creates ───→ Payment

Policy ───┬─ has many ──→ Claim
          └─ has many ──→ Payment

Claim ────┬─ belongs to → Policy
          └─ has many ──→ Payment

Payment ──┬─ belongs to → Claim
          ├─ belongs to → Policy
          └─ has many ──→ PaymentDetail

PaymentDetail ─ belongs to → Payment

Document ─┬─ attached to → Policy
          ├─ attached to → Claim
          └─ attached to → Payment

AuditLog ─ tracks ──→ All entities
```

## Security Architecture

### Authentication Flow

1. User registers with email/password
2. Password hashed with bcrypt
3. User logs in, receives JWT token
4. Token includes: user ID, email, role, expiration
5. Token valid for 60 minutes (configurable)
6. All protected endpoints verify token via `get_current_user_id` dependency

### Data Encryption

- **SSN/TIN**: Encrypted using Fernet symmetric encryption before storing
- **Banking Info**: Encrypted JSON objects for payment details
- **Tax ID Numbers**: Encrypted when stored
- **Masking**: SSN/TIN masked in responses (show only last 4 digits: `***-**-1234`)

### Authorization

- Role-based access control via JWT token claims
- Service layer enforces authorization rules
- Audit trail captures all user actions

## API Design

### REST Principles

- Resource-based URLs: `/policies`, `/claims`, `/payments`
- HTTP methods: GET (read), POST (create), PUT (update), DELETE (remove)
- Standard status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), 409 (Conflict), 500 (Internal Error)

### Response Format

**Success Response:**
```json
{
  "id": 123,
  "field1": "value1",
  "field2": "value2"
}
```

**Error Response:**
```json
{
  "status": 404,
  "error": "NOT_FOUND",
  "message": "Resource not found",
  "timestamp": "2026-03-01T12:00:00Z"
}
```

**Paginated Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 0,
  "size": 20,
  "pages": 5
}
```

## Middleware Stack

Middleware applied in order (outermost to innermost):

1. **RequestLoggingMiddleware**: Logs method, path, status, duration
2. **CorrelationIdMiddleware**: Propagates X-Correlation-Id header
3. **CORSMiddleware**: Handles cross-origin requests

## Exception Handling

### Exception Hierarchy

```
AppException (base)
├─ NotFoundException (404)
├─ ConflictException (409)
├─ AuthException (401)
├─ ForbiddenException (403)
└─ ValidationException (400)
```

All exceptions handled by `app_exception_handler`, returning standardized JSON error responses.

## Database Design

### Schema

- **users**: System users
- **policies**: Insurance policies
- **claims**: Claims linked to policies
- **payments**: Payments linked to claims and policies
- **payment_details**: Payment payees and portions
- **vendors**: Vendor/provider information
- **audit_logs**: Audit trail
- **documents**: File attachments

### Indexes

- Primary keys on all tables
- Foreign keys for relationships
- Indexes on: email (users), policy_number (policies), claim_number (claims), payment_number (payments)
- Composite indexes on search fields: first_name + last_name, city + state

### Audit Fields

All core entities include:
- `created_by`: User ID who created the record
- `updated_by`: User ID who last updated the record
- `created_at`: Timestamp (UTC)
- `updated_at`: Timestamp (UTC)

## Service Layer

### Service Modules

1. **auth_service**: User registration, login, token management
2. **policy_service**: Policy CRUD, search, SSN masking
3. **claim_service**: Claim CRUD, search, subrogation, claim-level policy data
4. **payment_service**: Payment CRUD, lifecycle (void/reverse/reissue), payment details
5. **vendor_service**: Vendor onboarding and management
6. **audit_service**: Audit log creation

### Service Responsibilities

- Business logic enforcement
- Data validation beyond schema validation
- Authorization checks
- Audit logging
- Error handling with typed exceptions

## Configuration Management

### Settings (app/config.py)

- **Environment-based**: Load from `.env` file or environment variables
- **Validation**: Pydantic Settings validates on startup
- **Secrets**: JWT secret, encryption key (must be overridden in production)
- **Database**: Connection URL (SQLite for dev, PostgreSQL for prod)
- **CORS**: Allowed origins
- **JWT**: Expiration time

### Environment Variables

```
APP_NAME=Integrated Policy Claims Payments Platform
ENVIRONMENT=development
DEBUG=False
DATABASE_URL=sqlite+aiosqlite:///./insurance_platform.db
JWT_SECRET=<secure-random-string>
JWT_EXPIRATION_MINUTES=60
ENCRYPTION_KEY=<secure-random-string>
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Health Checks

- **/health/live**: Liveness probe (always returns 200 OK)
- **/health/ready**: Readiness probe (checks database connectivity)

## Scalability Considerations

### Horizontal Scaling

- Stateless application design
- JWT tokens (no server-side session state)
- Database connection pooling

### Performance Optimization

- Async I/O throughout (FastAPI, SQLAlchemy async)
- Database indexes on search fields
- Pagination for all list endpoints
- Selective field loading (only fetch required columns)

### Future Enhancements

1. **Caching**: Redis for frequently accessed data
2. **Message Queue**: RabbitMQ/Kafka for async processing
3. **File Storage**: S3/Azure Blob for documents
4. **Database Sharding**: Partition by policy/claim range
5. **Read Replicas**: Separate read/write database instances

## Compliance & Standards

### PCI-DSS

- Encrypt payment data at rest
- Mask credit card numbers
- Secure transmission (HTTPS)
- Audit trail for all payment transactions

### WCAG Accessibility

- API responses include clear error messages
- Structured data format for screen readers

### Audit Requirements

- All actions logged with user ID and timestamp
- Immutable audit trail
- Change tracking with old/new values

## Deployment Architecture

### Development

```
Developer → Uvicorn (localhost:8000) → SQLite
```

### Production

```
Internet → Load Balancer → App Server (Uvicorn + Gunicorn) → PostgreSQL
                             ↓
                          Redis Cache
                             ↓
                      Message Queue (RabbitMQ)
```

## Technology Decisions

### Why FastAPI?

- Modern async Python framework
- Automatic OpenAPI/Swagger documentation
- Built-in request/response validation with Pydantic
- High performance (comparable to Node.js and Go)
- Type hints and IDE support

### Why SQLAlchemy Async?

- Mature ORM with excellent documentation
- Async support for high concurrency
- Database-agnostic (SQLite, PostgreSQL, MySQL)
- Alembic integration for migrations

### Why JWT?

- Stateless authentication
- Scalable (no server-side session storage)
- Standard format (RFC 7519)
- Self-contained (includes user info and expiration)

### Why Bcrypt?

- Industry standard for password hashing
- Adaptive cost factor (future-proof against hardware improvements)
- Salted automatically

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Summary

This architecture provides a secure, scalable, and maintainable platform for managing insurance policies, claims, and payments. The layered design with clear separation of concerns ensures code quality and testability. The use of modern Python async features enables high concurrency and performance.
