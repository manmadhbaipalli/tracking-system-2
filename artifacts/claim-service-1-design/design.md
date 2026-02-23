# Design: Integrated Policy, Claims, and Payments Platform

## Approach

### High-Level Solution Strategy

This design implements a comprehensive insurance management platform using **Domain-Driven Design (DDD)** principles with three core bounded contexts:

1. **Policy Domain** - Policy lifecycle management with advanced search capabilities
2. **Claims Domain** - Claims processing with policy linkage and audit trails
3. **Payments Domain** - Complex payment processing with compliance and integrations

**Architecture Pattern**: Clean Architecture with FastAPI
- **Presentation Layer**: FastAPI routes with Pydantic schemas
- **Application Layer**: Service classes with business logic
- **Domain Layer**: SQLAlchemy models with business rules
- **Infrastructure Layer**: Database, external integrations, utilities

**Key Design Decisions**:
- **Async-First**: All operations use async/await for scalability
- **Audit-by-Design**: Polymorphic audit model tracks all entity changes
- **Security-First**: Data masking, encryption, and role-based access built-in
- **Performance-Optimized**: Database indexes and query optimization for sub-5s response times
- **Integration-Ready**: Circuit breaker pattern for external system resilience

### Database Design Strategy

**Primary Entity Relationships**:
```
User (1) ←→ (N) AuditLog (polymorphic to all entities)
Policy (1) ←→ (N) Claim
Claim (1) ←→ (N) Payment
Payment (N) ←→ (N) Payee (joint payees)
```

**Audit Trail Approach**:
- Polymorphic audit table with `entity_type` and `entity_id` columns
- JSON field for `before_state` and `after_state` snapshots
- Automatic triggers via SQLAlchemy event listeners

**Search Optimization**:
- Composite indexes on frequently searched policy fields
- Full-text search indexes for name and address fields
- Partial indexes for active records only

## Detailed Changes

### Core Infrastructure Files

#### `app/main.py`
- FastAPI application factory with middleware stack
- CORS configuration for frontend integration
- Exception handlers for consistent error responses
- Route registration for all v1 endpoints
- OpenAPI documentation configuration
- Health check endpoint for monitoring

#### `app/core/config.py`
- Pydantic Settings model for environment-based configuration
- Database URLs for development (SQLite) and production (PostgreSQL)
- JWT secret key, algorithm, and expiration settings
- External integration credentials (Stripe, banking APIs)
- Logging configuration with structured output
- Performance settings (connection pools, timeouts)

#### `app/core/database.py`
- AsyncSession configuration with proper connection pooling
- Database engine creation with async PostgreSQL/SQLite support
- Session dependency for FastAPI routes
- Base model class with common fields (id, created_at, updated_at)
- Migration support with Alembic integration

#### `app/core/security.py`
- JWT token creation and verification functions
- Password hashing using passlib with bcrypt
- Role-based access control decorators (@require_role, @require_permissions)
- Current user dependency for route authentication
- Token refresh logic with blacklist support

### Database Models

#### `app/models/user.py`
```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### `app/models/audit.py`
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(index=True)  # "Policy", "Claim", etc.
    entity_id: Mapped[UUID] = mapped_column(index=True)
    action: Mapped[str]  # "CREATE", "UPDATE", "DELETE"
    before_state: Mapped[Optional[dict]] = mapped_column(JSON)
    after_state: Mapped[Optional[dict]] = mapped_column(JSON)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    ip_address: Mapped[Optional[str]]
    user_agent: Mapped[Optional[str]]
```

#### `app/models/policy.py`
- Policy master data with all required search fields
- Vehicle information embedded as JSON with validation
- Location details with separate address normalization
- Coverage details with limits and deductibles
- Composite indexes for search performance:
  - `(policy_number, policy_type)`
  - `(insured_last_name, insured_first_name)`
  - `(policy_state, policy_city)`
  - `(ssn_tin_hash)` for encrypted SSN/TIN lookups

#### `app/models/claim.py`
- Claims linked to policies via foreign key
- Claim-level policy data override fields (separate columns)
- Status workflow with state machine validation
- Subrogation support with related claim references
- Injury incident details as structured JSON
- Carrier involvement tracking

#### `app/models/payment.py`
- Payment transactions with complex state machine
- Multiple payee support via many-to-many relationship
- Reserve line allocation with erosion tracking
- Payment method abstraction for ACH, wire, cards, Stripe
- Void/reversal chain tracking for audit compliance
- Tax reporting fields with encrypted TIN storage

### API Schemas (Pydantic Models)

#### `app/schemas/policy.py`
```python
class PolicySearchRequest(BaseModel):
    policy_number: Optional[str] = None
    insured_first_name: Optional[str] = None
    insured_last_name: Optional[str] = None
    policy_type: Optional[str] = None
    loss_date: Optional[date] = None
    policy_city: Optional[str] = None
    policy_state: Optional[str] = None
    policy_zip: Optional[str] = None
    ssn_tin: Optional[str] = None  # Will be hashed for search
    organizational_name: Optional[str] = None

    class Config:
        # Validation for partial matches
        str_strip_whitespace = True

class PolicyResponse(BaseModel):
    id: UUID
    policy_number: str
    insured_name: str
    policy_type: str
    effective_date: date
    expiration_date: date
    policy_status: str
    ssn_tin_masked: str  # Always masked (XXX-XX-1234)
    # ... other fields with sensitive data properly masked
```

#### `app/schemas/claim.py`
- Request/response models for claim CRUD operations
- Claim history schemas with pagination support
- Policy override tracking in claim responses
- Status filtering and sorting parameters
- Audit trail inclusion options

#### `app/schemas/payment.py`
- Payment creation with multiple payment method support
- Payee allocation schemas with validation rules
- PCI-DSS compliant response models (no sensitive card data)
- Payment lifecycle tracking schemas
- Reserve allocation and erosion calculation models

### API Routes

#### `app/api/v1/policies.py`
**Endpoints**:
- `POST /api/v1/policies/search` - Advanced policy search with 9+ criteria
- `GET /api/v1/policies/{id}` - Policy details retrieval
- `POST /api/v1/policies` - Policy creation (admin only)
- `PUT /api/v1/policies/{id}` - Policy updates with audit
- `GET /api/v1/policies/{id}/claims` - Associated claims history

**Performance Requirements**:
- Policy search: 3-second response time maximum
- Policy details: 5-second response time maximum
- Pagination for large result sets (50 records per page)
- Database query optimization with proper indexes

#### `app/api/v1/claims.py`
**Endpoints**:
- `GET /api/v1/claims/{id}` - Claim details with policy association
- `POST /api/v1/claims` - Claim creation with policy linking
- `PUT /api/v1/claims/{id}` - Claim updates with audit trails
- `GET /api/v1/claims/{id}/history` - Claim modification history
- `PUT /api/v1/claims/{id}/policy-override` - Claim-level policy data updates
- `GET /api/v1/claims/search` - Claim search with status filtering

#### `app/api/v1/payments.py`
**Endpoints**:
- `POST /api/v1/payments` - Payment creation with method selection
- `GET /api/v1/payments/{id}` - Payment details with masked sensitive data
- `PUT /api/v1/payments/{id}/void` - Payment void operations
- `PUT /api/v1/payments/{id}/reverse` - Payment reversal processing
- `POST /api/v1/payments/{id}/reissue` - Payment reissue functionality
- `GET /api/v1/payments/search` - Payment search and filtering

### Business Services

#### `app/services/policy_service.py`
**Key Functions**:
```python
async def search_policies(
    search_criteria: PolicySearchRequest,
    db: AsyncSession,
    user: User,
    page: int = 1,
    limit: int = 50
) -> PolicySearchResponse:
    # Advanced search with partial matching
    # Performance-optimized queries with indexes
    # Audit logging for search operations
    # SSN/TIN hashing for secure lookups

async def get_policy_with_claims(
    policy_id: UUID,
    db: AsyncSession,
    user: User
) -> PolicyWithClaimsResponse:
    # Policy details with associated claims
    # Data masking for sensitive information
    # Role-based field access control
```

#### `app/services/claim_service.py`
**Key Functions**:
```python
async def create_claim_with_policy_override(
    claim_data: ClaimCreateRequest,
    policy_overrides: Optional[PolicyOverrideData],
    db: AsyncSession,
    user: User
) -> ClaimResponse:
    # Claim creation with optional policy data overrides
    # Audit trail for policy override tracking
    # Business rule validation

async def get_claim_history_sorted(
    claim_id: UUID,
    db: AsyncSession,
    status_filter: Optional[ClaimStatus] = None
) -> List[ClaimHistoryItem]:
    # Sorted by date of loss (most recent first)
    # Status filtering (Open, Closed, Paid, Denied)
    # Performance optimization for large claim histories
```

#### `app/services/payment_service.py`
**Key Functions**:
```python
async def create_payment_with_routing(
    payment_request: PaymentCreateRequest,
    db: AsyncSession,
    user: User
) -> PaymentResponse:
    # Payment creation with business rule routing
    # Multiple payment method support
    # PCI-DSS compliance validation
    # Reserve allocation and erosion tracking

async def process_payment_state_transition(
    payment_id: UUID,
    action: PaymentAction,
    db: AsyncSession,
    user: User
) -> PaymentResponse:
    # State machine for payment lifecycle
    # Audit trail for all state changes
    # Integration with external payment processors
```

### Utility Modules

#### `app/utils/audit.py`
**Functions**:
- Automatic audit trail creation via SQLAlchemy events
- Before/after state capture with field-level tracking
- User context propagation through async context
- Audit query utilities for compliance reporting

#### `app/utils/security.py`
**Functions**:
- SSN/TIN masking with consistent format (XXX-XX-1234)
- Payment card data masking (XXXX-XXXX-XXXX-1234)
- Field-level encryption for sensitive data at rest
- Role-based data access filtering

#### `app/utils/integrations.py`
**Functions**:
- Circuit breaker implementation for external APIs
- Retry logic with exponential backoff
- Stripe Connect integration for payment processing
- Banking API integration for ACH/wire transfers
- EDI 835/837 processing for medical providers

### Database Migration

#### `migrations/versions/001_initial_schema.py`
- Complete database schema creation
- All table definitions with proper constraints
- Index creation for performance optimization
- Foreign key relationships with cascade rules
- Initial data seeding (admin user, lookup tables)

## Interfaces

### Authentication & Authorization
```python
# JWT Token Structure
class TokenData(BaseModel):
    user_id: UUID
    email: str
    role: UserRole
    exp: datetime
    iat: datetime

# Role-Based Access Decorator
@require_role(UserRole.ADMIN, UserRole.CLAIMS_ADJUSTER)
async def admin_endpoint():
    pass
```

### API Response Standards
```python
# Standard Success Response
class APIResponse[T](BaseModel):
    success: bool = True
    data: T
    message: Optional[str] = None

# Standard Error Response
class APIError(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None
```

### Search Interface Pattern
```python
# All search endpoints follow this pattern
class SearchRequest(BaseModel):
    # Search criteria fields
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.ASC

class SearchResponse[T](BaseModel):
    items: List[T]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool
```

### Audit Trail Interface
```python
# All auditable entities implement this
class AuditableEntity:
    def create_audit_log(self, action: str, user: User, before: dict = None, after: dict = None)

# Audit context manager for service operations
async with audit_context(entity, action, user):
    # Perform operations
    # Audit log automatically created
```

### External Integration Interfaces
```python
# Payment processor interface
class PaymentProcessor(Protocol):
    async def process_payment(self, payment_request: PaymentRequest) -> PaymentResult
    async def void_payment(self, payment_id: str) -> VoidResult
    async def get_payment_status(self, payment_id: str) -> PaymentStatus

# Specific implementations: StripeProcessor, ACHProcessor, WireProcessor
```

## Trade-offs

### Architecture Decisions

**1. Monolithic vs Microservices**
- **Chosen**: Monolithic FastAPI application
- **Rationale**: Simpler deployment, shared database transactions, easier development
- **Trade-off**: Less independent scaling, but acceptable for initial implementation

**2. Database Design**
- **Chosen**: Single PostgreSQL database with domain separation by schema
- **Rationale**: ACID transactions across domains, simpler data consistency
- **Trade-off**: Potential for larger database, but better data integrity

**3. Audit Strategy**
- **Chosen**: Polymorphic audit table with JSON state snapshots
- **Rationale**: Flexible, supports all entities, easy to query
- **Trade-off**: Larger storage footprint vs. having separate audit tables per entity

**4. Authentication Approach**
- **Chosen**: JWT tokens with role-based access control
- **Rationale**: Stateless, scalable, easy integration with frontend
- **Trade-off**: Token revocation complexity vs. session-based auth simplicity

### Performance Trade-offs

**1. Search Performance**
- **Chosen**: Database indexes on all searchable fields
- **Rationale**: Meet 3-second search requirement
- **Trade-off**: Higher storage and slower writes vs. faster reads

**2. Audit Performance**
- **Chosen**: Async audit log creation with event listeners
- **Rationale**: Non-blocking audit trail creation
- **Trade-off**: Potential audit log delays vs. synchronous guaranteed logging

**3. Data Security**
- **Chosen**: Field-level encryption for sensitive data
- **Rationale**: PCI-DSS compliance and regulatory requirements
- **Trade-off**: Encryption/decryption overhead vs. data protection requirements

### Integration Trade-offs

**1. External Payment Processing**
- **Chosen**: Multiple payment processor support with adapter pattern
- **Rationale**: Flexibility and vendor redundancy
- **Trade-off**: Increased complexity vs. single vendor lock-in

**2. Circuit Breaker Pattern**
- **Chosen**: Circuit breakers for all external integrations
- **Rationale**: System resilience and graceful degradation
- **Trade-off**: Added complexity vs. system reliability

## Open Questions

### Implementation Decisions for Development Team

**1. Caching Strategy**
- Should we implement Redis caching for frequently accessed policies?
- What cache invalidation strategy should be used for policy updates?
- Consider: Memory usage vs. database load reduction

**2. File Upload Handling**
- How should document attachments be handled (local storage vs. cloud)?
- What file size limits should be enforced?
- Consider: Storage costs vs. user experience

**3. Logging and Monitoring**
- What level of structured logging is needed for production monitoring?
- Should we implement distributed tracing for payment workflows?
- Consider: Observability requirements vs. performance impact

**4. Testing Strategy**
- What level of test coverage is required for payment processing?
- How should external integration testing be handled (mocking vs. sandbox)?
- Consider: Test reliability vs. development velocity

**5. Deployment Configuration**
- Should we use environment-specific configuration files or environment variables?
- How should database migrations be handled in production deployments?
- Consider: Security vs. deployment simplicity

**6. Error Handling Granularity**
- How detailed should error messages be for different user roles?
- Should we implement user-friendly error messages vs. technical details?
- Consider: User experience vs. debugging capabilities

**7. Performance Monitoring**
- What metrics should be collected for the 3/5-second response time requirements?
- How should we handle performance degradation alerts?
- Consider: Monitoring overhead vs. SLA compliance

### Security Implementation Details

**1. Encryption Key Management**
- How should encryption keys be rotated for field-level encryption?
- Should we use a key management service or local key storage?

**2. Audit Log Retention**
- How long should audit logs be retained?
- Should older audit logs be archived or purged?

**3. Payment Data Compliance**
- What specific PCI-DSS requirements need custom implementation vs. library support?
- How should payment card data be handled during processing?

These open questions should be resolved during implementation based on specific deployment requirements, compliance needs, and performance testing results.