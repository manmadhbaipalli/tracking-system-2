# Design: claim-service-2 - Integrated Policy, Claims, and Payments Platform

## Approach

This design implements a comprehensive integrated platform for managing insurance policies, claims, and payments by building upon the existing solid architectural foundation. The approach follows a **layered architecture** with clear separation of concerns:

1. **Service Layer First**: Implement complete business logic in service classes before API endpoints
2. **Database-Driven Design**: Leverage existing comprehensive models with proper migrations and indexing
3. **Security by Design**: Integrate audit logging, data masking, and encryption throughout
4. **Performance Optimization**: Implement caching, connection pooling, and query optimization
5. **Integration Architecture**: Use circuit breakers and retry logic for external system resilience

The implementation strategy prioritizes **core functionality first** (Policy → Claims → Payments) followed by advanced integrations, ensuring a functional baseline before complex external system dependencies.

## Detailed Changes

### Phase 1: Core Service Layer Implementation

#### 1. Policy Service (`app/services/policy_service.py`)
**Current State**: All methods return `NotImplementedError`
**Required Changes**:
- **Advanced Search Algorithm**: Implement multi-criteria search with SQL query building for exact/partial matches across 9+ fields
- **Performance Optimization**: Use composite database indexes and query optimization for 3-second response requirement
- **CRUD Operations**: Full create/read/update/delete with proper validation and business rules
- **Audit Integration**: Automatic audit trail generation using `app.utils.audit` utilities
- **Data Security**: Integration with `app.utils.security` for SSN/TIN encryption and masking

```python
# Key implementation pattern:
async def search_policies(self, search_criteria: PolicySearchRequest) -> List[Policy]:
    query = select(Policy)
    if search_criteria.policy_number:
        query = query.where(Policy.policy_number.like(f"%{search_criteria.policy_number}%"))
    # ... additional criteria with optimized joins and indexes
    result = await self.db.execute(query)
    return result.scalars().all()
```

#### 2. Claim Service (`app/services/claim_service.py`)
**Current State**: All methods return `NotImplementedError`
**Required Changes**:
- **Policy-Claim Relationships**: Implement complex relationship management with claim-level policy overrides
- **Effective Policy Resolution**: Logic to determine whether to use original policy data or claim-level overrides
- **Subrogation Workflow**: Complete business logic for subrogation referral process
- **Status Management**: Claim lifecycle state machine with validation rules
- **History Tracking**: Comprehensive audit trail for all claim modifications

#### 3. Payment Service (`app/services/payment_service.py`)
**Current State**: All methods return `NotImplementedError`
**Required Changes**:
- **Payment State Machine**: Complex lifecycle management (created → processed → void/reversed → reissued)
- **Multiple Payment Methods**: Support for ACH, wire, cards, Stripe Connect with method-specific validation
- **Reserve Allocation**: Logic for allocating payments across multiple reserve lines with erosion tracking
- **Tax Compliance**: Withholding calculations and tax reportable designation
- **Multi-Payee Support**: Payment splitting and joint payee management

### Phase 2: Database Infrastructure

#### 4. Database Migrations Setup (`migrations/env.py`, `alembic.ini`)
**Current State**: No migration infrastructure exists
**Required Changes**:
- **Alembic Configuration**: Set up async-compatible migration environment
- **Environment Management**: Support for development (aiosqlite) and production (PostgreSQL) databases
- **Connection Handling**: Proper async session management during migrations

#### 5. Initial Schema Migration (`migrations/versions/001_initial_schema.py`)
**Current State**: No database tables exist
**Required Changes**:
- **Table Creation**: Generate complete schema from existing models
- **Performance Indexes**: Create composite indexes for policy search optimization:
  - `(policy_state, policy_city, policy_zip)`
  - `(insured_last_name, insured_first_name)`
  - `(policy_type, policy_status, effective_date)`
- **Relationship Constraints**: Proper foreign key relationships with cascading rules

### Phase 3: API Endpoint Implementation

#### 6. Policy API (`app/api/v1/policies.py`)
**Current State**: All endpoints return 501 Not Implemented
**Required Changes**:
- **CRUD Endpoints**: Replace all 501 responses with proper service integration
- **Validation Layer**: Request/response validation using existing Pydantic schemas
- **Error Handling**: Specific error messages per BRD requirements
- **Role-Based Access**: Integration with authentication and authorization
- **Performance Requirements**: Ensure 3-second response for search operations

#### 7. Claim API (`app/api/v1/claims.py`)
**Current State**: All endpoints return 501 Not Implemented
**Required Changes**:
- **Policy Integration**: Endpoints that properly handle claim-policy relationships
- **Audit Access**: Endpoints for accessing comprehensive audit trails
- **Status Filtering**: Claim listing with proper status-based filtering
- **History Endpoints**: Policy claim history with 5-second response requirement

#### 8. Payment API (`app/api/v1/payments.py`)
**Current State**: All endpoints return 501 Not Implemented (assumed from pattern)
**Required Changes**:
- **Lifecycle Management**: Full payment processing, void, reversal, and reissue endpoints
- **Method-Specific Processing**: ACH, wire, card, and Stripe Connect handling
- **Compliance Endpoints**: Tax withholding and reporting functionality
- **Multi-Payee Management**: Endpoints for payment allocation and joint payee handling

### Phase 4: Infrastructure Enhancements

#### 9. External Integrations (`app/utils/integrations.py`, `app/utils/external_systems.py`)
**Current State**: Stub implementations with circuit breaker patterns
**Required Changes**:
- **Stripe Connect**: Complete payment processing with webhook handling
- **Banking Systems**: ACH and wire transfer integration with secure credential handling
- **Xactimate Integration**: Automated estimate import with data transformation
- **EDI 835/837**: Medical provider integration with proper formatting
- **Document Management**: File attachment and retrieval capabilities

#### 10. Security Enhancements (`app/utils/security.py`)
**Current State**: Basic utilities exist
**Required Changes**:
- **Data Masking**: Comprehensive SSN/TIN masking for API responses
- **Encryption**: At-rest encryption for sensitive payment and personal data
- **Compliance Functions**: PCI-DSS validation and audit support

#### 11. Infrastructure Components (`app/core/database.py`, `app/core/config.py`, `app/api/deps.py`)
**Current State**: Basic implementations exist
**Required Changes**:
- **Connection Pooling**: Optimize for concurrent user sessions
- **Configuration Management**: Environment-specific settings for all integrations
- **Enhanced Authentication**: Improved JWT validation and role management

## Interfaces

### New API Interfaces

#### Policy Search Response
```python
class PolicySearchResponse(BaseModel):
    policies: List[PolicyResponse]
    total_count: int
    page: int
    page_size: int
    search_criteria: PolicySearchRequest
    execution_time_ms: int  # Performance tracking
```

#### Claim History Response
```python
class ClaimHistoryResponse(BaseModel):
    claims: List[ClaimResponse]
    policy_id: UUID
    total_count: int
    filtered_by_status: Optional[str]
    sorted_by: str = "date_of_loss_desc"
```

#### Payment Allocation Interface
```python
class PaymentAllocation(BaseModel):
    payee_id: UUID
    amount: Decimal
    reserve_line_id: UUID
    erosion_type: str  # "eroding" | "non_eroding"
    tax_withholding: Optional[Decimal]
    tax_reportable: bool
```

### Enhanced Service Interfaces

#### Audit Context Interface
```python
class AuditContext:
    user_id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    changes: Dict[str, Any]
    timestamp: datetime
```

#### Search Performance Interface
```python
class SearchPerformance:
    criteria_count: int
    query_execution_time_ms: int
    result_count: int
    index_usage: List[str]
```

### External System Interfaces

#### Stripe Integration Response
```python
class StripePaymentResponse:
    payment_intent_id: str
    status: str
    amount: Decimal
    fees: Decimal
    metadata: Dict[str, str]
```

## Trade-offs

### Architecture Decisions

#### 1. Service Layer First vs. API First
**Chosen**: Service layer implementation before API endpoints
**Rationale**: Ensures proper business logic separation and testability
**Trade-off**: Slightly longer time to visible API functionality
**Benefits**: Cleaner architecture, easier testing, better maintainability

#### 2. Comprehensive Migration vs. Incremental Schema
**Chosen**: Single comprehensive migration with all tables
**Rationale**: Existing models are complete and well-designed
**Trade-off**: Larger initial migration file
**Benefits**: Simpler deployment, all relationships established correctly

#### 3. Real-time Integration vs. Batch Processing
**Chosen**: Real-time integration with circuit breakers
**Rationale**: BRD requires 5-second payment processing response
**Trade-off**: Higher complexity in error handling
**Benefits**: Better user experience, immediate feedback

#### 4. Database Connection Strategy
**Chosen**: Async connection pooling with session per request
**Rationale**: Concurrent user requirement and async FastAPI framework
**Trade-off**: More complex session management
**Benefits**: Better performance under load, proper resource management

### Security vs. Performance Trade-offs

#### Encryption Strategy
**Decision**: Encrypt sensitive fields at application layer rather than database layer
**Rationale**: Better control over encryption keys and compliance auditing
**Trade-off**: Slight performance impact on queries involving encrypted fields
**Mitigation**: Use selective encryption only for truly sensitive data (SSN/TIN, banking info)

#### Audit Logging Granularity
**Decision**: Comprehensive audit trail for all operations
**Rationale**: Regulatory compliance and business requirements
**Trade-off**: Increased storage requirements and slight performance impact
**Mitigation**: Async audit logging and efficient audit table design

## Open Questions

### Implementation Decisions for Implementation Agent

#### 1. Database Index Strategy
**Question**: Should we create all possible composite indexes upfront or add them incrementally based on performance testing?
**Recommendation**: Create core search indexes in initial migration, add specialized indexes as needed
**Context**: Policy search with 9+ criteria requires careful index design for 3-second response requirement

#### 2. External System Error Handling
**Question**: How aggressively should we retry failed external system calls (Stripe, banking, etc.)?
**Recommendation**: Implement exponential backoff with max 3 retries, fail fast for critical payment operations
**Context**: Balance between reliability and user experience for 5-second payment processing requirement

#### 3. Claim-Level Policy Override Storage
**Question**: Should claim-level policy overrides be stored as JSON or separate normalized tables?
**Recommendation**: Use JSON storage for flexibility, with proper indexing for searchability
**Context**: Business requirement for tracking changes without overwriting original policy data

#### 4. Payment State Machine Implementation
**Question**: Should payment state transitions be enforced at database level or application level?
**Recommendation**: Application-level enforcement with database constraints as backup
**Context**: Complex payment lifecycle with void/reversal/reissue operations

#### 5. Integration Testing Strategy
**Question**: Should external system integrations be tested with real APIs or mocked services during development?
**Recommendation**: Use mocked services for development, real API testing for final validation
**Context**: Stripe, banking, and EDI systems have different testing environments and costs

#### 6. Performance Monitoring
**Question**: Should we implement detailed performance monitoring and metrics collection?
**Recommendation**: Yes, especially for search operations and external system response times
**Context**: Specific performance requirements (3-second search, 5-second details/payments)

#### 7. Concurrent Payment Processing
**Question**: How should we handle concurrent payment processing to prevent race conditions?
**Recommendation**: Use database transactions with proper locking for payment state changes
**Context**: Multiple users may process payments for the same claim simultaneously

### Configuration Decisions

#### 8. Environment-Specific Settings
**Question**: What configuration values should be environment-specific vs. hardcoded?
**Recommendation**: All external system credentials, database URLs, and performance tuning parameters should be configurable
**Context**: Development vs. production environments will have different requirements

#### 9. Caching Strategy
**Question**: Should we implement caching for frequently accessed data (policies, lookup tables)?
**Recommendation**: Implement Redis caching for read-heavy operations after basic functionality is complete
**Context**: Performance requirements may benefit from caching, but adds complexity