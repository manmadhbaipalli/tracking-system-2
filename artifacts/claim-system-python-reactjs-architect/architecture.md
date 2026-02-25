# Architecture: Integrated Policy, Claims, and Payments Platform
## claim-system-python-reactjs

**Document Version:** 1.0
**Date:** 2026-02-24
**Prepared By:** SmartArchitect Agent

---

## 1. Architecture Overview

### Style: Layered Monolith with Clean Architecture Elements

**Rationale:**
- **Single Deployment Unit**: Simpler deployment, monitoring, and debugging for Phase 1
- **Clear Layer Boundaries**: Enforces separation of concerns (Controller → Service → Repository)
- **Scalability Path**: Stateless design enables horizontal scaling; can evolve to microservices later
- **Domain Complexity**: Complex business rules (premium calculation, reserve allocation, payment routing) benefit from layered organization
- **Team Structure**: Team can work independently on different layers (frontend, API, business logic, data access)
- **Performance**: Monolith avoids inter-service latency; local function calls are faster than REST calls
- **Clean Architecture Elements**: Services use domain-driven design for claims, payments, and premium calculations

### Component Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Frontend (ReactJS 18+)                          │
│  ┌─────────────────┐ ┌──────────────────┐ ┌─────────────────────────┐ │
│  │  Policy Pages   │ │  Claims Pages    │ │  Payments Pages         │ │
│  │  (Search, View) │ │  (FNOL, Adjust)  │ │  (Create, Approve)      │ │
│  └────────┬────────┘ └────────┬─────────┘ └────────────┬────────────┘ │
├───────────┼──────────────────┼────────────────────────┼───────────────┤
│           │ HTTP/HTTPS (JSON) │                        │               │
│           └──────────┬───────────────────────────────┬─────────────────┤
│                      │ /api/v1/                      │                 │
│                      ↓                               ↓                 │
│           ┌──────────────────────────────────────────────────┐         │
│           │           API Layer (Controllers)                │         │
│           │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │         │
│           │  │ AuthCtrl │ │PolicyCtrl│ │ ClaimCtrl Paymet │ │         │
│           │  │          │ │          │ │ AdminCtrl etc.   │ │         │
│           │  └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │         │
│           │       │            │                │            │         │
│           ├───────┼────────────┼────────────────┼────────────┤         │
│           │       ↓            ↓                ↓            │         │
│           │  ┌─────────────────────────────────────────────┐ │         │
│           │  │    Service Layer (Business Logic)          │ │         │
│           │  │ ┌─────────┐ ┌──────────┐ ┌────────────────┐│ │         │
│           │  │ │PolicySvc│ │ClaimSvc  │ │PaymentSvc      ││ │         │
│           │  │ │Premium  │ │Reserve   │ │Payee etc.      ││ │         │
│           │  │ │Endorsmnt│ │Audit     │ │RBAC            ││ │         │
│           │  │ └────┬────┘ └────┬─────┘ └────────┬───────┘│ │         │
│           │  └──────┼───────────┼────────────────┼────────┘ │         │
│           │         │           │                │           │         │
│           ├─────────┼───────────┼────────────────┼───────────┤         │
│           │         ↓           ↓                ↓           │         │
│           │  ┌──────────────────────────────────────────────┐ │         │
│           │  │   Repository Layer (Data Access)            │ │         │
│           │  │ ┌──────────┐ ┌────────────┐ ┌───────────────┐│ │         │
│           │  │ │PolicyRepo│ │ClaimRepo   │ │PaymentRepo    ││ │         │
│           │  │ │PayeeRepo │ │UserRepo    │ │AuditLogRepo   ││ │         │
│           │  │ └────┬─────┘ └────┬───────┘ └───────┬───────┘│ │         │
│           │  └──────┼────────────┼─────────────────┼────────┘ │         │
│           └─────────┼────────────┼─────────────────┼──────────┘         │
│                     │            │                 │                    │
├────────────────────┼────────────┼─────────────────┼────────────────────┤
│                    ↓            ↓                 ↓                    │
│         ┌──────────────────────────────────────────────────────┐       │
│         │          SQLAlchemy ORM Models                       │       │
│         │  User, Policy, Claim, Payment, Payee, Audit, etc.   │       │
│         └──────────────────────────────────────────────────────┘       │
│                             ↓                                          │
│         ┌──────────────────────────────────────────────────────┐       │
│         │      PostgreSQL 16 (Prod) / SQLite 3 (Dev)           │       │
│         └──────────────────────────────────────────────────────┘       │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Cross-Cutting Concerns (Middleware, Utilities)                 │ │
│  │  ┌────────────┐ ┌─────────────┐ ┌──────────────┐ ┌───────────┐ │ │
│  │  │JWT/Auth    │ │Logging      │ │Error Handler │ │Encryption │ │ │
│  │  │RBAC        │ │Correlation  │ │Custom Exc.   │ │Masking    │ │ │
│  │  │            │ │ID Middleware│ │Global        │ │Validators │ │ │
│  │  └────────────┘ └─────────────┘ └──────────────┘ └───────────┘ │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  External Integrations (Async via Celery)                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────┐ ┌───────────────────┐ │ │
│  │  │Stripe    │ │Global    │ │Tax ID/KYC   │ │ACH/Wire/Doc Mgmt  │ │ │
│  │  │Connect   │ │Payouts   │ │Verification │ │Xactimate/Acctng   │ │ │
│  │  └──────────┘ └──────────┘ └─────────────┘ └───────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Supporting Services                                            │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐ │ │
│  │  │Redis     │ │Celery    │ │Health    │ │Audit Logging       │ │ │
│  │  │Cache     │ │Async Queue   │Checks   │ │(Immutable Store)  │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Decisions

| Category | Decision | Rationale |
|----------|----------|-----------|
| **Language** | Python 3.12 | Mature, excellent ecosystem for data/business logic; async support; team familiarity implied by requirements |
| **Framework** | FastAPI 0.100+ | High performance (async/await); auto-generated OpenAPI/Swagger; Pydantic integration; excellent for APIs |
| **Database (Prod)** | PostgreSQL 16 | ACID-compliant, JSON support, full-text search, mature ecosystem; ACORD standard |
| **Database (Dev)** | SQLite 3 | Zero setup, file-based, ideal for local development and testing |
| **ORM** | SQLAlchemy 2.0 | Industry standard; relationship management; migration support via Alembic; type hints |
| **Validation** | Pydantic v2 | Type-safe, auto-generated OpenAPI docs, validation at API boundary |
| **Authentication** | JWT (Bearer tokens) | Stateless, scalable, no server-side session storage, ideal for distributed systems |
| **Password Hashing** | bcrypt (strength 10+) | Industry standard, slow hash resists brute force attacks |
| **Async Queue** | Celery 5.3+ + Redis 7+ | Industry-standard for Python async tasks; handles long-running payment processing, notifications |
| **Caching** | Redis 7+ | Sub-millisecond performance; ideal for search results, session data, rate limiting |
| **Logging** | structlog + JSON | Structured logs for correlation ID tracing, production monitoring, audit trail analysis |
| **HTTP Server** | Uvicorn (dev) + Gunicorn (prod) | ASGI-compliant; Gunicorn with worker pool for production concurrency |
| **Migrations** | Alembic | Version-controlled schema changes; reversible migrations |
| **Testing** | pytest + pytest-asyncio | Python standard; excellent async support; fixture system |
| **API Documentation** | FastAPI auto-generated Swagger/OpenAPI | Zero-effort, always in sync with code |
| **Code Quality** | Black (formatter) + Ruff (linter) | Fast, opinionated formatting; Rust-based linter for speed |

---

## 3. Component Design

### 3.1 Controller Layer (`routers/`)

**Purpose:** HTTP request handling, input validation, response serialization

**Components:**
- `auth.py` — POST /register, /login (JWT token generation)
- `policies.py` — GET/POST/PUT /policies (policy CRUD, search, endorsement)
- `claims.py` — GET/POST/PUT /claims (claim FNOL, investigation, settlement)
- `payments.py` — GET/POST/PUT /payments (payment creation, approval, processing)
- `payees.py` — GET/POST/PUT /payees (payee onboarding, KYC)
- `admin.py` — Routing rules, user management, payment method config
- `health.py` — /health/live, /health/ready (liveness/readiness probes)
- `audit.py` — GET /audit-logs (audit trail retrieval)

**Dependencies:** Service layer, Pydantic schemas, Security (JWT/RBAC)

**Public API:**
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/policies (search: ?policy_number=, &insured_name=, &status=, etc.)
GET    /api/v1/policies/{id}
POST   /api/v1/policies
PUT    /api/v1/policies/{id}
POST   /api/v1/policies/{id}/endorsements
POST   /api/v1/policies/{id}/renewals
POST   /api/v1/claims
GET    /api/v1/claims (search: ?claim_number=, &status=, &date_range=, etc.)
GET    /api/v1/claims/{id}
PUT    /api/v1/claims/{id}
POST   /api/v1/payments
GET    /api/v1/payments
PUT    /api/v1/payments/{id}/approve
PUT    /api/v1/payments/{id}/reverse
GET    /api/v1/payees
POST   /api/v1/payees
GET    /api/v1/health/live
GET    /api/v1/health/ready
GET    /api/v1/audit-logs
```

**Error Responses:** Standardized format with 400/401/403/404/422/500 status codes

---

### 3.2 Service Layer (`services/`)

**Purpose:** Business logic, transaction management, domain rules

**Components:**
- `policy_service.py` — Policy CRUD, premium calculation, endorsement, renewal, cancellation
- `claim_service.py` — Claim FNOL, investigation, adjustment, settlement, denial, reopening
- `payment_service.py` — Payment creation, approval, processing, reversal, reissue, void
- `payee_service.py` — Payee onboarding, KYC verification, payment method management
- `premium_service.py` — Premium calculation engine (formula: Base × Territory × Age × Claims - Discounts + Surcharges)
- `reserve_service.py` — Reserve tracking, allocation, adjustment, line management
- `audit_service.py` — Audit log creation, retrieval, PII masking
- `rbac_service.py` — User role/permission management, permission enforcement

**Dependencies:** Repository layer, Domain models, Custom exceptions, Utils (encryption, masking)

**Key Business Logic:**
- **Premium Calculation** (PRM-001 to PRM-010):
  ```
  total_premium = (base_rate × territory_factor × age_factor × claims_factor)
                  - discounts + surcharges
  min_premium = $100
  ```
- **Reserve Calculation** (CLM-006):
  ```
  reserve = min(claimed_amount, coverage_limit) - deductible
  settlement = min(reserve, approved_amount)
  ```
- **Payment Allocation** (PAY-006):
  ```
  Σ(allocation per reserve line) = payment_amount
  reserve_balance_new = previous_balance - allocated_amount (if eroding)
  ```

---

### 3.3 Repository Layer (`repositories/`)

**Purpose:** Data access, CRUD operations, query abstraction

**Components:**
- `base.py` — BaseRepository with generic CRUD operations (create, read, update, delete, find_by)
- `policy_repo.py` — PolicyRepository with search, find_by_number, find_by_insured
- `claim_repo.py` — ClaimRepository with search, find_by_policy, find_by_status
- `payment_repo.py` — PaymentRepository with find_pending_approval, find_by_status
- `payee_repo.py` — PayeeRepository with find_by_tax_id, find_unverified
- `user_repo.py` — UserRepository for RBAC (find_by_email, find_by_role)
- `audit_repo.py` — AuditLogRepository with search, filter by date range/entity type

**Dependencies:** SQLAlchemy ORM, Database session

**Public API:**
- `create(obj: Model) → Model`
- `read(id: int) → Model`
- `update(id: int, obj: Model) → Model`
- `delete(id: int) → bool`
- `find_all(skip: int, limit: int) → List[Model]`
- `find_by(field: str, value: any) → List[Model]`
- `search(filters: dict) → List[Model]` (entity-specific filters)

---

### 3.4 Model Layer (`models/`)

**Purpose:** SQLAlchemy ORM entity definitions with relationships

**Entities** (~15 total):
1. `User` — Application users (username, email, password_hash, role_id, active, created_at, updated_at)
2. `Role` — RBAC roles (AGENT, UNDERWRITER, CLAIMS_ADJUSTER, FINANCE_MANAGER, RECOVERY_MANAGER, ADMIN, AUDITOR)
3. `Permission` — Granular permissions (READ_POLICY, CREATE_CLAIM, APPROVE_PAYMENT, etc.)
4. `Insured` — Party data (first_name, last_name, ssn_tin, email, phone, address, date_of_birth, organization_name)
5. `Policy` — Policy record (policy_number, insured_id, policy_type, status, effective_date, expiration_date, aggregate_limit, total_premium, term_length)
6. `Coverage` — Coverage details per policy (coverage_type, limit_amount, deductible_amount, premium_portion, status)
7. `Premium` — Premium calculation record (base_rate, territory_factor, age_factor, claims_factor, discounts, surcharges, total_premium)
8. `Endorsement` — Mid-term policy change (endorsement_number, policy_id, status, endorsement_type, effective_date, premium_change)
9. `Claim` — Claim record (claim_number, policy_id, status, date_of_loss, loss_type, claimed_amount, reserve_amount, settlement_amount, paid_amount)
10. `ClaimAdjustment` — Claim adjustment history (claim_id, adjustment_type, previous_amount, new_amount, reason, adjusted_by, created_at)
11. `ReserveLine` — Reserve breakdown (claim_id, reserve_type, estimated_amount, current_balance, paid_to_date)
12. `Payee` — Vendor/claimant (payee_type, legal_name, tax_id, status, kyc_verified_date, address, email, phone, payment_methods)
13. `PaymentMethod` — Payment account per payee (payee_id, method_type, account_number, routing_number, account_type, verified_date)
14. `Payment` — Payment transaction (claim_id, policy_id, payee_id, payment_type, status, payment_amount, deductions, net_amount, payment_method, eroding_flag, reference_number)
15. `AuditLog` — Immutable audit trail (user_id, user_role, action, entity_type, entity_id, before_values, after_values, ip_address, timestamp)

**Base Class:**
```python
class BaseEntity(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**Key Relationships:**
- Policy → Insured (many-to-one)
- Policy → Coverage (one-to-many)
- Policy → Claim (one-to-many)
- Claim → ReserveLine (one-to-many)
- Payment → Claim (many-to-one)
- Payment → Payee (many-to-one)
- Payee → PaymentMethod (one-to-many)

---

### 3.5 Schema Layer (`schemas/`)

**Purpose:** Pydantic DTOs for request/response validation and OpenAPI documentation

**Schemas** (~20+):
- `auth.py` — RegisterRequest, LoginRequest, LoginResponse (with access_token)
- `policy.py` — PolicyCreate, PolicyUpdate, PolicyResponse, PolicySearchFilter
- `claim.py` — ClaimFNOL, ClaimUpdate, ClaimResponse, ClaimSearchFilter
- `payment.py` — PaymentCreate, PaymentResponse, PaymentApprovalRequest
- `payee.py` — PayeeOnboarding, KYCVerificationRequest, PaymentMethodCreate
- `common.py` — PaginationResponse, ErrorResponse, PageResponse, HealthStatus

**Example Structure:**
```python
class PolicyCreate(BaseModel):
    policy_type: PolicyType  # Enum: AUTO, HOME, LIFE, HEALTH, COMMERCIAL
    insured_id: int
    effective_date: date
    expiration_date: date
    aggregate_limit: Decimal  # Stored as string in JSON
    total_premium: Decimal
    term_length: TermLength  # Enum: 6_MONTHS, 12_MONTHS

class PolicyResponse(PolicyCreate):
    policy_id: int
    policy_number: str  # Format: POL-YYYY-NNNNNN
    status: PolicyStatus  # Enum: QUOTED, BOUND, ISSUED, ACTIVE, CANCELLED, EXPIRED
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    status: int
    error: str
    message: str
    details: List[ErrorDetail]  # [{field, message}]
    timestamp: datetime
    correlation_id: str
```

---

### 3.6 Security Layer (`security.py`)

**Purpose:** JWT authentication, password hashing, RBAC enforcement

**Components:**
- `generate_access_token(user_id, role, exp_seconds=3600)` — Generate JWT with claims
- `verify_token(token) → claims` — Decode and validate JWT
- `hash_password(password) → hashed` — bcrypt with strength 10
- `verify_password(password, hashed) → bool`
- `get_current_user() → User` — Dependency for protected endpoints
- `require_permission(permission_name)` — Decorator for endpoint-level RBAC
- `mask_pii(data) → masked_data` — SSN/account masking for display

**JWT Claims:**
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "CLAIMS_ADJUSTER",
  "permissions": ["READ_CLAIM", "UPDATE_CLAIM", "APPROVE_PAYMENT"],
  "iat": 1708713000,
  "exp": 1708716600
}
```

**Token Storage (Frontend):**
- Access token in memory (expires in 15-60 min)
- Refresh token in httpOnly cookie (optional, expires in 7-30 days)

---

### 3.7 Middleware & Cross-Cutting Concerns (`middleware.py`, `utils/`)

**Middleware:**
- **CorrelationIdMiddleware** — Extract/generate X-Correlation-Id header, add to all logs
- **LoggingMiddleware** — Log all requests/responses with method, path, status, duration
- **ExceptionHandlerMiddleware** — Catch exceptions, convert to standardized error responses

**Utilities:**
- `encryption.py` — AES-256 encrypt/decrypt for SSN, bank account numbers, tax IDs
- `masking.py` — Mask SSN (XXX-XX-1234), account (****7890), tokens in logs
- `validators.py` — Validate business rules (coverage limit ≤ policy limit, deductible ≤ limit, etc.)
- `formatters.py` — Format Decimal as string in JSON, format dates as ISO 8601

---

## 4. Data Flow

### 4.1 Policy Creation Flow
```
POST /api/v1/policies (PolicyCreate DTO)
    ↓ FastAPI validates JSON via Pydantic
Controller (PolicyRouter)
    ↓ calls PolicyService.create_policy(dto, current_user)
Service (PolicyService)
    ↓ validates business rules (effective_date ≥ today, etc.)
    ↓ calls premium_service.calculate_premium()
    ↓ generates Policy Number (POL-YYYY-NNNNNN)
    ↓ calls policy_repo.create(policy_obj)
Repository (PolicyRepository)
    ↓ calls db.session.add(policy)
    ↓ calls db.session.commit()
SQLAlchemy ORM
    ↓ generates SQL INSERT statement
    ↓ executes against PostgreSQL
Database (PostgreSQL)
    ↓ inserts row, generates id
    ↓ returns to ORM
ORM → Repository → Service → Controller
    ↓ calls audit_service.log_action(user, CREATE, POLICY, policy_id, before={}, after={policy_data})
Audit Service
    ↓ creates AuditLog record (immutable)
    ↓ returns PolicyResponse DTO
Controller
    ↓ serializes to JSON
    ↓ returns 201 Created response
Client (Frontend)
    ↓ displays confirmation
```

### 4.2 Claim Payment Processing Flow
```
POST /api/v1/payments (PaymentCreate DTO)
    ↓ Controller validates input
    ↓ calls PaymentService.create_payment(dto, current_user)
Service (PaymentService)
    ↓ validates: payee verified, payment ≤ settlement, claim SETTLED
    ↓ calls reserve_service.allocate_payment(payment_obj, reserve_lines)
    ↓ creates Payment record with status=DRAFT
    ↓ returns PaymentResponse
Controller
    ↓ returns 201 Created
    ↓
PUT /api/v1/payments/{id}/approve (payment approval threshold > $5,000)
    ↓ Controller validates: current_user has APPROVE_PAYMENT permission
    ↓ calls PaymentService.approve_payment(payment_id, current_user)
Service (PaymentService)
    ↓ updates Payment.status = PENDING_APPROVAL → APPROVED
    ↓ Celery async task: payment_processing_task.delay(payment_id)
    ↓ returns PaymentResponse
Controller
    ↓ returns 200 OK
    ↓
Celery Task (Async)
    ↓ retrieves Payment from DB
    ↓ validates Payee (must be VERIFIED)
    ↓ calls PaymentService.process_payment(payment_obj)
    ↓ calls appropriate processor:
       ├─ if ACH: ach_wire_service.generate_ach_file()
       ├─ if Wire: ach_wire_service.create_wire_instruction()
       ├─ if Stripe: stripe_service.create_payout()
       └─ if Global Payouts: global_payouts_service.route_payment()
    ↓ receives confirmation_number from processor
    ↓ updates Payment.status = PROCESSING → PROCESSED
    ↓ updates Payment.reference_number = confirmation_number
    ↓ calls reserve_service.update_reserve(claim_id, allocated_amounts) (if eroding)
    ↓ calls audit_service.log_action(user, PROCESS, PAYMENT, payment_id, ...)
    ↓ sends notification via notification_service.notify_payee(payee, payment_obj)
    ↓ task complete
```

---

## 5. Security Architecture

### 5.1 Authentication

**Method:** JWT Bearer tokens (stateless)

**Flow:**
1. User submits email + password → POST /auth/register or /auth/login
2. Backend validates credentials (password match via bcrypt)
3. Backend generates JWT access token (15-60 min expiration)
4. Optional refresh token (7-30 days) in httpOnly cookie
5. Client includes `Authorization: Bearer <token>` in all requests
6. Backend validates token signature + expiration

**Token Structure:**
```json
Header: {"alg": "HS256", "typ": "JWT"}
Payload: {
  "sub": "12345",
  "email": "user@example.com",
  "role": "CLAIMS_ADJUSTER",
  "permissions": ["READ_CLAIM", "UPDATE_CLAIM", "APPROVE_PAYMENT"],
  "iat": 1708713000,
  "exp": 1708716600
}
Signature: HMACSHA256(Base64(Header) + "." + Base64(Payload), JWT_SECRET)
```

**JWT Secret Management:**
- Minimum 32 characters
- Stored in environment variable `JWT_SECRET` (not in code)
- Rotated annually (coordinate with all running instances)

### 5.2 Authorization (Role-Based Access Control)

**Roles** (7 total):
1. **AGENT** — Create quotes, bind policies, search own policies
2. **UNDERWRITER** — Issue policies, approve endorsements, underwrite claims
3. **CLAIMS_ADJUSTER** — Create claims, investigate, adjust reserves, settle
4. **FINANCE_MANAGER** — Create payments, approve threshold payments, configure methods
5. **RECOVERY_MANAGER** — Manage subrogation cases, recovery tracking
6. **ADMIN** — User management, role assignment, configuration, audit logs
7. **AUDITOR** — Read-only access to audit logs, reports

**Permission Model:**
```
User → Role (many-to-many)
Role → Permission (many-to-many)

Permissions: READ_POLICY, CREATE_POLICY, UPDATE_POLICY, APPROVE_POLICY, etc.
```

**Endpoint Access Matrix:**

| Endpoint | Public | AGENT | UNDERWRITER | CLAIMS_ADJUSTER | FINANCE_MANAGER | ADMIN | AUDITOR |
|----------|--------|-------|-------------|-----------------|-----------------|-------|---------|
| POST /auth/register | ✓ | — | — | — | — | — | — |
| POST /auth/login | ✓ | — | — | — | — | — | — |
| GET /api/v1/policies | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| POST /api/v1/policies | — | ✓ | — | — | — | ✓ | — |
| PUT /api/v1/policies/{id} | — | ✓ | — | — | — | ✓ | — |
| POST /api/v1/policies/{id}/endorsements | — | ✓ | ✓ | — | — | ✓ | — |
| POST /api/v1/claims | — | — | — | ✓ | — | ✓ | — |
| GET /api/v1/claims | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| PUT /api/v1/claims/{id} | — | — | — | ✓ | — | ✓ | — |
| POST /api/v1/payments | — | — | — | ✓ | ✓ | ✓ | — |
| PUT /api/v1/payments/{id}/approve | — | — | — | — | ✓ | ✓ | — |
| GET /api/v1/audit-logs | — | — | — | — | — | ✓ | ✓ |

**Enforcement:**
- API-level: `@require_permission("READ_POLICY")` decorator on endpoints
- Query-level: Filter results by user's authorized scope (e.g., adjuster sees only assigned claims)
- Returns 403 Forbidden if permission denied

### 5.3 Data Encryption & Masking

**At-Rest Encryption** (Database):
- Sensitive fields encrypted with AES-256:
  - `ssn_tin` → `Insured.ssn_tin_encrypted` (decrypted only when needed)
  - `account_number` → `PaymentMethod.account_number_encrypted`
  - `tax_id` → `Payee.tax_id_encrypted`
- Encryption key stored in KMS (AWS Secrets Manager / Azure Key Vault)
- Key rotation policy: annually

**In-Transit Encryption:**
- All API traffic: HTTPS/TLS 1.2+
- Database connections: SSL/TLS
- Message queues: encrypted

**Data Masking** (Display):
- SSN display: `XXX-XX-1234` (last 4 digits visible)
- Account display: `****7890` (last 4 digits visible)
- Tokens: never logged or displayed
- Audit logs: sensitive data masked

**OWASP API Top 10 Mitigations:**

| Vulnerability | Mitigation |
|---|---|
| Broken OLBA (Object Level) | Service layer checks resource ownership (e.g., adjuster can only view assigned claims) |
| Broken Auth | JWT validation, bcrypt, token expiration, session timeout (30 min inactivity) |
| Broken BLPA (Property Level) | DTOs filter sensitive fields (never expose `password_hash`, `ssn_plain`) |
| Unrestricted Resources | Pagination limits (max 100), query size limits, rate limiting (1000 req/min per user) |
| Broken Function Auth | RBAC on endpoints, @require_permission decorators |
| Unrestricted Biz Flows | Rate limiting at API gateway level; circuit breaker for payment processors |
| SSRF | No user-supplied URLs in backend calls; whitelist external endpoints |
| Security Misconfiguration | CORS whitelist (prod: specific origins), actuator security, error hiding (no stack traces in prod) |
| Improper Inventory | API versioning (/api/v1/), OpenAPI docs, deprecated endpoint warnings |
| Unsafe Consumption | Validate external API responses, retry logic with exponential backoff |

### 5.4 Input Validation

**Validation Boundary:** API endpoint (Pydantic schemas)

**Validation Rules:**
- Email format: `EmailStr` (Pydantic)
- Date: ISO 8601 format
- Decimal amounts: String with 2 decimal places
- Enum values: Whitelist (PolicyType ∈ {AUTO, HOME, LIFE, HEALTH, COMMERCIAL})
- Length limits: Text fields have max length

**SQL Injection Prevention:** SQLAlchemy ORM uses parameterized queries (no string concatenation)

**XSS Prevention:** JSON-only API (no HTML rendering); Frontend handles escaping

---

## 6. Observability Strategy

### 6.1 Logging

**Framework:** structlog (structured JSON logging)

**Format (Production):**
```json
{
  "timestamp": "2026-02-24T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.services.payment_service",
  "message": "Payment processed successfully",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "12345",
  "user_role": "CLAIMS_ADJUSTER",
  "entity_type": "PAYMENT",
  "entity_id": "98765",
  "action": "PROCESS",
  "duration_ms": 234,
  "payment_method": "ACH",
  "reference_number": "ACH123456789"
}
```

**Format (Development):** Human-readable key=value pairs

**Log Levels:**
- **DEBUG** — Development only; detailed variable states
- **INFO** — Business events: policy created, claim settled, payment processed
- **WARNING** — Degraded state: slow query, external service latency
- **ERROR** — Failures: payment processing error, database connection lost
- **CRITICAL** — System-level failures: database unavailable, KMS unreachable

**PII Masking in Logs:**
- SSN: `XXX-XX-1234`
- Account: `****7890`
- Email: `u***@example.com` (first letter + domain)
- Tokens: `[REDACTED]`

**Output:** stdout (container logs aggregated by log shipper)

### 6.2 Correlation IDs

**Purpose:** Trace requests across services and log aggregation

**Generation:** UUID v4 per incoming HTTP request

**Propagation:**
- Extract from incoming `X-Correlation-Id` header (if provided)
- Generate new UUID if header missing
- Add to response `X-Correlation-Id` header
- Include in all log statements via MDC (Mapped Diagnostic Context)
- Pass to async tasks in Celery
- Pass to external API calls in Authorization header

**Example Log Trail:**
```
Request → /api/v1/payments (X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000)
Log: Payment.create_payment() [correlation_id: 550e8400...]
Log: PaymentService.allocate_reserves() [correlation_id: 550e8400...]
Log: PaymentRepository.create() [correlation_id: 550e8400...]
Celery Task → processing payment [correlation_id: 550e8400...]
Log: StripeService.create_payout() [correlation_id: 550e8400...]
Response ← 201 Created [X-Correlation-Id: 550e8400...]
```

### 6.3 Health Checks

**Liveness Probe** (`GET /health/live`):
```json
{"status": "alive", "timestamp": "2026-02-24T10:30:00Z"}
```
- Simple 200 OK; app is running
- Used by Kubernetes to restart failed instances

**Readiness Probe** (`GET /health/ready`):
```json
{
  "status": "ready",
  "database": "healthy",
  "redis": "healthy",
  "timestamp": "2026-02-24T10:30:00Z"
}
```
- Checks: database connection, Redis connectivity
- Returns 200 OK if all services healthy; 503 if any unhealthy
- Used by load balancer to route traffic

---

## 7. Configuration Strategy (12-Factor App)

### 7.1 Environment Variables

**Development (.env file):**
```
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET=dev-secret-min-32-chars-1234567890
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=DEBUG
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
```

**Production (Environment Variables):**
```
DATABASE_URL=postgresql://user:password@prod-db.amazonaws.com:5432/claim_system_prod
JWT_SECRET=<production-secret-from-kms>
CORS_ORIGINS=https://app.example.com,https://portal.example.com
LOG_LEVEL=INFO
REDIS_URL=redis://prod-redis.amazonaws.com:6379/0
CELERY_BROKER_URL=redis://prod-redis.amazonaws.com:6379/0
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### 7.2 Pydantic Settings Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"
    jwt_secret: str = Field(min_length=32, default="dev-secret-min-32-chars-1234567890")
    jwt_expiration: int = 3600  # seconds
    cors_origins: List[str] = ["http://localhost:3000"]
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 7.3 Profiles

**Development:**
- Database: SQLite (in-memory or file-based)
- Debug: True, detailed error messages
- CORS: Permissive (localhost:3000, localhost:5173)
- Logging: DEBUG level, human-readable

**Production:**
- Database: PostgreSQL managed instance
- Debug: False, minimal error details
- CORS: Strict whitelist (specific domains)
- Logging: INFO level, JSON format
- SSL/TLS: Enforced

---

## 8. Database Design

### 8.1 Entity Relationships

```
User (1) ──── (many) Role
Role (1) ──── (many) Permission
User (many) ──── (many) Permission (via Role)

Insured (1) ──── (many) Policy
Policy (1) ──── (many) Coverage
Policy (1) ──── (many) Claim
Policy (1) ──── (many) Endorsement
Policy (1) ──── (many) Premium

Claim (1) ──── (many) ClaimAdjustment
Claim (1) ──── (many) ReserveLine
Claim (1) ──── (many) Payment
Claim (1) ──── (many) ScheduledPayment
Claim (1) ──── (many) Subrogation

Payee (1) ──── (many) PaymentMethod
Payee (1) ──── (many) Payment
Payment (many) ──── (many) ReserveLine (via PaymentAllocation)

All Entities (1) ──── (many) AuditLog (immutable)
```

### 8.2 Key Constraints

- **Primary Keys:** Auto-incrementing integer `id`
- **Foreign Keys:** Cascade delete disabled (soft references via repository)
- **Unique Constraints:** policy_number, claim_number, endorsement_number, payee_tax_id
- **Non-Null Constraints:** Required business fields (policy_number, effective_date, created_at, etc.)
- **Check Constraints:** aggregate_limit > 0, effective_date <= expiration_date

### 8.3 Indexing Strategy

```sql
CREATE INDEX idx_policies_insured_id ON policies(insured_id);
CREATE INDEX idx_policies_policy_number ON policies(policy_number);
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_claims_policy_id ON claims(policy_id);
CREATE INDEX idx_claims_claim_number ON claims(claim_number);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_payments_claim_id ON payments(claim_id);
CREATE INDEX idx_payments_payee_id ON payments(payee_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_audit_logs_entity_id ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
```

---

## 9. Error Handling Strategy

### 9.1 Exception Hierarchy

```
Exception (built-in)
├── AppException (base, 500 Internal Server Error)
│   ├── ValidationException (400 Bad Request)
│   ├── AuthenticationException (401 Unauthorized)
│   ├── AuthorizationException (403 Forbidden)
│   ├── NotFoundException (404 Not Found)
│   ├── ConflictException (409 Conflict)
│   ├── UnprocessableEntityException (422 Unprocessable Entity)
│   │   ├── PolicyRuleViolation (e.g., coverage > aggregate limit)
│   │   ├── ClaimBusinessRuleViolation (e.g., claim on expired policy)
│   │   └── PaymentRuleViolation (e.g., payment > settlement)
│   └── InternalServerError (500 Internal Server Error)
│       ├── PaymentProcessingException (payment processor error)
│       ├── ExternalServiceException (external API failure)
│       └── DatabaseException (database error)
```

### 9.2 Global Exception Handler

**Endpoint:** FastAPI @app.exception_handler

**Behavior:**
1. Catch exception type
2. Map to HTTP status code
3. Log error with correlation_id
4. Mask sensitive data in error message
5. Return standardized ErrorResponse

**Error Response Format:**
```json
{
  "status": 422,
  "error": "Unprocessable Entity",
  "message": "Coverage limit cannot exceed policy aggregate limit",
  "details": [
    {
      "field": "coverage_limit",
      "message": "2000000 exceeds aggregate limit 1000000"
    }
  ],
  "timestamp": "2026-02-24T10:30:00Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 9.3 Business Rule Error Messages

| Error | HTTP | Message | User-Facing |
|---|---|---|---|
| Policy not found | 404 | Policy with ID 123 not found | "Policy not found" |
| Coverage > aggregate | 422 | Coverage limit $2M exceeds policy aggregate $1M | "Coverage limit exceeds policy aggregate limit" |
| Claim on expired policy | 422 | Cannot file claim on policy expired > 90 days ago | "Cannot file claim on expired policy" |
| Payment > settlement | 422 | Payment $10k exceeds settlement $8k | "Payment amount exceeds claim settlement" |
| Payee not verified | 422 | Payee 456 status is PENDING_VERIFICATION | "Payee not verified for payment" |
| No matching policies | 200 | Empty result set | "No matching policies found" |
| System unavailable | 503 | Database connection failed | "System is currently unavailable" |

---

## 10. API Design Principles

### 10.1 RESTful Conventions

| Method | Endpoint | Action | Status | Body |
|--------|----------|--------|--------|------|
| POST | /api/v1/policies | Create policy | 201 | PolicyResponse |
| GET | /api/v1/policies | List (search) | 200 | List[PolicyResponse] |
| GET | /api/v1/policies/{id} | Retrieve | 200 | PolicyResponse |
| PUT | /api/v1/policies/{id} | Update | 200 | PolicyResponse |
| DELETE | /api/v1/policies/{id} | Delete (if allowed) | 204 | — |
| POST | /api/v1/policies/{id}/endorsements | Create endorsement | 201 | EndorsementResponse |
| POST | /api/v1/claims | Create claim (FNOL) | 201 | ClaimResponse |
| PUT | /api/v1/claims/{id} | Update claim | 200 | ClaimResponse |

### 10.2 Pagination

**Query Parameters:**
```
GET /api/v1/policies?offset=0&limit=25&sort_by=created_at&sort_order=desc
```

**Response Envelope:**
```json
{
  "data": [/* array of items */],
  "pagination": {
    "offset": 0,
    "limit": 25,
    "total": 147,
    "has_more": true
  }
}
```

**Limits:**
- Default limit: 25
- Max limit: 100
- Min offset: 0

### 10.3 Versioning

**Version in URL:** `/api/v1/`, `/api/v2/` (if needed in future)

**Backward Compatibility:** New fields added as optional; deprecated fields marked with warning

### 10.4 Documentation

**Auto-Generated:**
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

**Coverage:** 100% of public endpoints auto-documented from Pydantic schemas and endpoint docstrings

---

## 11. Integration Architecture

### 11.1 External System Integration Pattern

```
Application Service
    ↓ calls IntegrationService.process_payment(payment_obj)
    ↓ validates parameters
    ↓ calls PaymentProcessor.submit(request)
    ↓
Retry Handler (Exponential Backoff)
    ├─ Attempt 1: 0s delay
    ├─ Attempt 2: 1s delay (if timeout/5xx)
    ├─ Attempt 3: 2s delay (if timeout/5xx)
    └─ Fail after 3 attempts
    ↓
Circuit Breaker
    ├─ Healthy: 0 consecutive failures → CLOSED (accept requests)
    ├─ Degraded: 5 consecutive failures → OPEN (reject fast)
    └─ Half-Open: Try 1 request; success → CLOSED, fail → OPEN
    ↓
External API Call (HTTP POST / Webhook)
    ↓ Timeout: 30s
    ↓ Response validation: JSON schema validation
    ↓ Error handling: Parse error response, retry if 5xx
    ↓ Success: Extract confirmation number, store in Payment
    ↓
Application
```

### 11.2 Supported Integrations

| Integration | Method | Purpose | Error Handling |
|---|---|---|---|
| Stripe Connect | REST API (OAuth) | Payout to connected accounts | Retry + circuit breaker |
| Global Payouts | REST API | Multi-currency payouts | Retry + circuit breaker |
| ACH Provider | File upload + webhook | ACH batch processing | File validation, confirmation webhook |
| Wire Transfer | REST API | Wire transfer instruction | Retry + manual confirmation |
| Xactimate | File upload (JSON/XML) | Estimate parsing | Schema validation, line item extraction |
| Tax ID Verifier | REST API (IRS/SSA) | Payee tax ID validation | Cached results, fallback to manual |
| Document Management | REST API / S3 | Document storage | Retry, encryption at rest |
| Accounting System | REST API | Journal entry posting | Retry, reconciliation check |

---

## 12. Performance Targets (NFRs)

| Requirement | Target | Strategy |
|---|---|---|
| Policy search results | < 3 seconds | Indexed queries, Redis cache, pagination |
| Policy detail view | < 5 seconds | Lazy loading, relationship caching |
| Claim retrieval | < 5 seconds | Indexed queries, Redis cache |
| Premium calculation | < 2 seconds | In-memory formula, no external calls |
| Payment processing | < 5 seconds | Async via Celery (background) |
| Concurrent users | 1000+ sessions | Stateless design, read replicas, connection pooling |
| API CRUD operations | < 500ms | Indexed queries, minimal joins |

---

## 13. Deployment & DevOps (Architectural Notes)

### 13.1 Container Image
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 13.2 Local Development (Docker Compose)
```yaml
version: '3.9'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/claim_system_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
  postgres:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=claim_system_dev
    ports:
      - "5432:5432"
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

### 13.3 Production Deployment (Kubernetes)
- Horizontal Pod Autoscaling (HPA): Scale based on CPU/memory
- Readiness/Liveness probes: `/health/ready`, `/health/live`
- Resource limits: CPU 1.0, Memory 1Gi
- Init container: Alembic migrations (run DB schema updates on startup)

---

## 14. Future Extensibility

1. **Microservices Migration**: Extract Payment Service, Claim Service as separate deployments
2. **Event-Driven Architecture**: Add event bus (RabbitMQ, Kafka) for pub/sub
3. **GraphQL**: Add GraphQL layer alongside REST for flexible queries
4. **Mobile App**: Dedicated mobile API endpoints
5. **Analytics**: Separate analytics database (ClickHouse, BigQuery)
6. **AI/ML**: Claim fraud detection, premium recommendation engine

---

End of Architecture Document
