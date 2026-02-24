# Integrated Policy, Claims, and Payments Platform - Architecture Document

## Architecture Overview

### Architecture Style: Layered Monolith

**Rationale:** The system requires complex domain logic with tight integration between policies, claims, and payments. While the domain is sophisticated, there's no requirement for independent deployment of modules. A layered monolith provides:
- Strong consistency across policy-claim-payment relationships
- Simplified transaction management for financial operations
- Reduced complexity compared to microservices
- Better performance for complex queries spanning multiple entities
- Easier development and debugging during initial implementation

**Component Diagram (Text-based):**
```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │    Auth     │ │   Policies  │ │   Claims & Payments     │ │
│  │ /auth/login │ │ /policies   │ │   /claims /payments     │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ AuthService │ │PolicyService│ │ ClaimService            │ │
│  │             │ │             │ │ PaymentService          │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Model Layer (SQLAlchemy)                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │    User     │ │   Policy    │ │   Claim → Payment       │ │
│  │   AuditLog  │ │   Vehicle   │ │   Payee → PaymentMethod │ │
│  │             │ │   Coverage  │ │   Reserve → Settlement  │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                           │
│              PostgreSQL 16 (prod) / SQLite (dev)           │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### API Layer (app/api/)
**Purpose:** REST endpoint definitions, request/response validation, OpenAPI documentation
**Dependencies:** Service layer, schema validation (Pydantic), authentication utilities
**Public API:** HTTP endpoints following REST conventions with `/api/v1/` prefix

**Components:**
- `auth.py` — Authentication endpoints (login, register, refresh)
- `users.py` — User management endpoints
- `policies.py` — Policy search, CRUD operations
- `claims.py` — Claim management and status updates
- `payments.py` — Payment processing and lifecycle management
- `health.py` — Health check endpoints for monitoring

### Service Layer (app/services/)
**Purpose:** Business logic implementation, external integrations, transaction management
**Dependencies:** Model layer, external APIs, audit logging
**Public API:** Business operation methods with async/await patterns

**Components:**
- `auth_service.py` — Authentication business logic, password validation
- `policy_service.py` — Policy search optimization, business rule validation
- `claim_service.py` — Claim workflow management, status transitions
- `payment_service.py` — Payment processing, external gateway integration
- `audit_service.py` — Cross-cutting audit logging for all operations

### Model Layer (app/models/)
**Purpose:** Data persistence, relationships, constraints, business rules at data level
**Dependencies:** SQLAlchemy, database connection
**Public API:** SQLAlchemy ORM models with relationships and validation

**Components:**
- `base.py` — Abstract base model with audit fields
- `user.py` — User authentication and role management
- `policy.py` — Policy entity with related vehicles, locations, coverages
- `claim.py` — Claim entity with policy relationships and overrides
- `payment.py` — Complex payment structures with multi-payee support
- `audit.py` — Audit trail for all data modifications

### Schema Layer (app/schemas/)
**Purpose:** Request/response validation, API contract definition, data transformation
**Dependencies:** Pydantic, type validation
**Public API:** Pydantic models for API serialization/deserialization

### Core Layer (app/core/)
**Purpose:** Application configuration, database sessions, security utilities
**Dependencies:** Environment variables, SQLAlchemy, JWT libraries
**Public API:** Configuration objects, database session factories, security functions

### Utils Layer (app/utils/)
**Purpose:** Cross-cutting concerns, utilities, external integrations
**Dependencies:** Encryption libraries, HTTP clients, logging
**Public API:** Utility functions for encryption, audit, integrations

## Data Flow

**Request Flow Example: Policy Search**
1. **Client** → `GET /api/v1/policies/search?insured_first_name=John`
2. **API Layer** → `policies.py` validates request, checks authentication
3. **Service Layer** → `policy_service.search_policies()` applies business logic
4. **Model Layer** → SQLAlchemy query with proper joins and indexing
5. **Database** → Optimized query execution with response time < 3 seconds
6. **Response Path** → Results formatted via Pydantic schemas, sensitive data masked

**Payment Processing Flow:**
1. **API Layer** → Validates payment request with multi-payee structure
2. **Service Layer** → `payment_service.create_payment()` starts database transaction
3. **Business Logic** → Validates reserve balances, applies payment rules
4. **External Integration** → Calls Stripe/bank APIs with circuit breaker pattern
5. **Database Updates** → Updates payment, reserve, audit records in single transaction
6. **Audit Trail** → Logs all changes with correlation ID for traceability

## Technology Decisions

| Category | Decision | Rationale |
|----------|----------|-----------|
| **Language** | Python 3.11+ | Established choice, async support, rich ecosystem for financial apps |
| **Framework** | FastAPI 0.100+ | High performance, native async, auto-generated OpenAPI docs |
| **Database** | PostgreSQL 16 (prod), aiosqlite (dev) | ACID compliance, JSON support, async drivers, proven reliability |
| **ORM** | SQLAlchemy 2.0+ with async | Mature relationship handling, complex query support, async native |
| **Authentication** | python-jose + passlib | JWT token support, BCrypt hashing, FastAPI integration |
| **API Documentation** | FastAPI auto-generated OpenAPI | Built-in, no additional dependencies, Swagger UI included |
| **Migrations** | Alembic | SQLAlchemy integration, version control for schema changes |
| **Validation** | Pydantic 2.0+ | Type safety, FastAPI native integration, performance optimized |
| **Logging** | structlog | Structured JSON logging, correlation ID support |
| **Testing** | pytest + pytest-asyncio | Async test support, comprehensive fixture system |
| **External Payments** | Stripe Connect, async HTTP clients | PCI-compliant, global support, webhook integration |

## Security Architecture

### Authentication Strategy
- **JWT Access Tokens:** 15-60 minutes expiration (configurable)
- **Refresh Tokens:** 7-30 days for persistent sessions
- **Password Security:** BCrypt hashing with 12 rounds minimum
- **Token Structure:** `{"sub": user_id, "role": "ADMIN|AGENT|ADJUSTER|VIEWER", "iat": timestamp, "exp": timestamp}`

### Authorization Matrix (RBAC)
| Resource/Action | VIEWER | AGENT | ADJUSTER | ADMIN |
|-----------------|--------|-------|----------|-------|
| **Authentication** |
| Login/Logout | ✓ | ✓ | ✓ | ✓ |
| Register Users | ✗ | ✗ | ✗ | ✓ |
| **Policies** |
| View/Search | ✓ | ✓ | ✓ | ✓ |
| Create/Update | ✗ | ✓ | ✓ | ✓ |
| Delete | ✗ | ✗ | ✗ | ✓ |
| **Claims** |
| View | ✓ | ✓ | ✓ | ✓ |
| Create/Update | ✗ | ✗ | ✓ | ✓ |
| Status Changes | ✗ | ✗ | ✓ | ✓ |
| **Payments** |
| View | ✓ | ✓ | ✓ | ✓ |
| Create/Process | ✗ | ✗ | ✓ | ✓ |
| Void/Reverse | ✗ | ✗ | ✓ | ✓ |

### OWASP API Security Top 10 Mitigations
1. **Broken Object Level Authorization** → Resource ownership checks in service layer
2. **Broken Authentication** → JWT validation, secure token generation, BCrypt hashing
3. **Broken Object Property Level Authorization** → Pydantic schema filtering, never expose password_hash or full SSN
4. **Unrestricted Resource Consumption** → Pagination limits (max 100), query timeouts
5. **Broken Function Level Authorization** → Role-based endpoint access, middleware enforcement
6. **Unrestricted Access to Sensitive Business Flows** → Rate limiting on auth endpoints
7. **Server Side Request Forgery** → No user-supplied URLs in backend API calls
8. **Security Misconfiguration** → CORS whitelist, no debug in production, secure headers
9. **Improper Inventory Management** → API versioning (/api/v1/), comprehensive OpenAPI docs
10. **Unsafe Consumption of APIs** → Validate all external API responses, timeout handling

### Input Validation & Data Security
- **Request Validation:** All endpoints use Pydantic schemas for comprehensive validation
- **SQL Injection Prevention:** SQLAlchemy ORM with parameterized queries only
- **XSS Prevention:** JSON-only API responses, no HTML rendering
- **Data Masking:** SSN/TIN display only last 4 digits in all user interfaces
- **Data Encryption:** AES-256 (Fernet) for sensitive data at rest
- **Transport Security:** TLS 1.3 for all communications

## Observability Strategy

### Structured Logging
- **Format:** JSON in production for machine parsing, readable format in development
- **Correlation IDs:** UUID generated per request, propagated through all operations
- **Log Levels:**
  - ERROR: System failures, integration errors, unrecoverable exceptions
  - WARN: Performance degradation, external service timeouts, business rule violations
  - INFO: User actions, payment processing, status changes
  - DEBUG: Request/response details, query performance (development only)
- **Security:** Never log passwords, full SSN/TIN, JWT tokens, payment card details

### Health Check Strategy
- **Liveness Check:** `/health/live` → Simple 200 OK response (app is running)
- **Readiness Check:** `/health/ready` → Database connectivity, external service status
- **Dependency Checks:** PostgreSQL connection, Redis cache (if implemented), external API connectivity
- **Response Format:** JSON with status and individual component health

### Correlation and Tracing
- **Request Correlation:** `X-Correlation-Id` header generated for each request
- **Context Propagation:** Python contextvars for async-safe correlation ID propagation
- **Audit Integration:** All audit logs include correlation ID for end-to-end traceability
- **External Integration:** Correlation ID passed to external APIs where supported

### Metrics and Monitoring
- **API Metrics:** Request count, response time percentiles (50th, 95th, 99th), error rates
- **Business Metrics:** Policies created, claims processed, payments completed, search performance
- **Infrastructure Metrics:** Database connection pool utilization, memory usage, CPU usage
- **Integration Metrics:** External API response times, circuit breaker status, retry counts

## Configuration Management

### Environment Variable Strategy
Following 12-Factor App principles with Pydantic Settings validation:

| Variable | Description | Default | Environment |
|----------|-------------|---------|-------------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./dev.db` | All |
| `JWT_SECRET_KEY` | JWT signing key (base64 encoded) | **Required in production** | All |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `60` | All |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `30` | All |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000"]` | All |
| `LOG_LEVEL` | Logging level | `INFO` | All |
| `ENVIRONMENT` | Environment profile | `development` | All |
| `ENCRYPTION_KEY` | Fernet encryption key | **Required in production** | All |
| `STRIPE_SECRET_KEY` | Stripe API secret key | Optional | Production |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification | Optional | Production |

### Environment Profiles
- **Development:** SQLite database, debug logging, relaxed CORS, mock external services
- **Staging:** PostgreSQL database, info logging, restricted CORS, test external services
- **Production:** PostgreSQL cluster, warn/error logging, strict CORS, production external services

### Secrets Management
- **Development:** `.env` file (not committed to repository)
- **Production:** Environment variables injected by deployment platform
- **Key Rotation:** JWT keys and encryption keys support rotation without downtime
- **External Secrets:** Stripe keys, database credentials managed by secure secret management

## Database Design

### Entity Relationships (High-Level)
```
User (1) ←→ (N) AuditLog
  │
  └─── Tracks all changes

Policy (1) ←→ (N) Claim
  │              │
  ├── (N) Vehicle    ├── (N) Payment
  ├── (N) Location   ├── (N) Reserve
  ├── (N) Coverage   └── (N) ClaimPolicyOverride
  └── (N) AuditLog

Payment (1) ←→ (N) PaymentPayee
  │                    │
  └── (N) PaymentReserveAllocation
                       │
                    Payee (1) ←→ (N) PaymentMethod
```

### Data Consistency Strategy
- **ACID Transactions:** All payment operations wrapped in database transactions
- **Optimistic Locking:** Version fields on critical entities (Policy, Claim, Payment)
- **Referential Integrity:** Foreign key constraints enforced at database level
- **Audit Trail:** All changes tracked with before/after values and user context

### Performance Optimization
- **Indexes:** Composite indexes on search-heavy fields (policy search criteria)
- **Connection Pooling:** SQLAlchemy async connection pool with configurable limits
- **Query Optimization:** Eager loading for related entities, pagination for large result sets
- **Caching Strategy:** Application-level caching for reference data (future enhancement)

## Error Handling Strategy

### Exception Hierarchy
```python
class ClaimSystemException(Exception):
    """Base exception for all business logic errors"""

class ValidationError(ClaimSystemException):
    """Data validation failures"""

class AuthorizationError(ClaimSystemException):
    """Permission denied, insufficient role"""

class BusinessRuleError(ClaimSystemException):
    """Business rule violations"""

class IntegrationError(ClaimSystemException):
    """External service failures"""

class NotFoundError(ClaimSystemException):
    """Resource not found"""
```

### Global Exception Handling
- **HTTP Exception Handler:** Converts business exceptions to appropriate HTTP status codes
- **Validation Errors:** 422 with field-specific error details
- **Authorization Errors:** 403 with generic "insufficient permissions" message
- **Not Found Errors:** 404 with resource-specific messages
- **Internal Errors:** 500 with correlation ID, no stack traces in production

### Error Response Format
```json
{
  "error": {
    "code": "BUSINESS_RULE_VIOLATION",
    "message": "Payment amount exceeds available reserve balance",
    "correlation_id": "uuid-here",
    "field_errors": [
      {
        "field": "total_amount",
        "message": "Amount $5000 exceeds reserve balance $3000"
      }
    ]
  }
}
```

## API Design Principles

### RESTful Conventions
- **Resource-Based URLs:** `/api/v1/policies/{id}/claims` not `/api/v1/getClaimsForPolicy`
- **HTTP Methods:** GET (read), POST (create), PUT (update), DELETE (remove)
- **Status Codes:** Appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 422, 500)
- **Content Type:** `application/json` for all requests and responses

### API Versioning Strategy
- **URL Versioning:** `/api/v1/` prefix for all endpoints
- **Backward Compatibility:** Maintain v1 compatibility during v2 development
- **Deprecation Policy:** 6-month notice for breaking changes
- **Version Headers:** Optional `API-Version` header support

### Pagination and Filtering
- **Default Pagination:** 20 items per page, maximum 100 per page
- **Pagination Format:** `?page=1&limit=20` query parameters
- **Response Envelope:** `{"data": [...], "pagination": {"total": 100, "page": 1, "limit": 20}}`
- **Filtering:** Query parameters for search criteria (`?status=OPEN&date_from=2024-01-01`)

### Response Consistency
- **Success Responses:** Data in `data` field, metadata in separate fields
- **Error Responses:** Error details in `error` field with consistent structure
- **Timestamps:** ISO 8601 format with timezone information
- **Currency:** Decimal strings for monetary values to avoid floating-point precision issues

---

## Implementation Priorities

### Phase 1: Core Foundation (Weeks 1-2)
- Authentication and authorization system
- Basic policy management (create, read, update)
- Database models and migrations
- Health checks and logging

### Phase 2: Claims Management (Weeks 3-4)
- Claim creation and status management
- Claim-policy relationships
- Basic audit logging
- Policy search functionality

### Phase 3: Payment Processing (Weeks 5-6)
- Payment creation and basic processing
- Multi-payee support
- Reserve allocation
- External integration framework

### Phase 4: Advanced Features (Weeks 7-8)
- Payment lifecycle management (void, reverse)
- Advanced search and filtering
- Settlement management
- Performance optimization

This architecture provides a solid foundation for the integrated policy, claims, and payments platform while maintaining flexibility for future enhancements and scalability requirements.