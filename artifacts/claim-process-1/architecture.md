# Architecture Document
## Integrated Policy, Claims, and Payments Platform

### Overview
This document describes the architecture and design decisions for the Integrated Policy, Claims, and Payments Platform, a comprehensive insurance management system built with Python and FastAPI.

### Technology Stack

#### Backend Framework
- **FastAPI 0.115+**: Modern, high-performance web framework with automatic API documentation
- **Python 3.11+**: Latest stable Python with async/await support

#### Database
- **SQLAlchemy 2.0**: Async ORM for database operations
- **SQLite** (development): File-based database for local development
- **PostgreSQL** (production): Scalable relational database for production deployments
- **Alembic**: Database migration management

#### Security
- **Passlib + Bcrypt**: Password hashing with industry-standard algorithm
- **Python-JOSE**: JWT token generation and validation
- **Cryptography/Fernet**: Symmetric encryption for sensitive data (SSN/TIN, banking info)

#### Validation & Configuration
- **Pydantic v2**: Request/response validation and settings management
- **Pydantic Settings**: Environment-based configuration with validation

#### Testing
- **Pytest**: Test framework
- **Pytest-asyncio**: Async test support
- **Pytest-cov**: Code coverage reporting

### Architecture Patterns

#### 1. Layered Architecture
```
┌─────────────────────────────────────┐
│      API Layer (Routers)            │  ← HTTP handlers, validation
├─────────────────────────────────────┤
│      Service Layer (Business Logic) │  ← Domain logic, orchestration
├─────────────────────────────────────┤
│      Data Layer (Models/Repository) │  ← Database operations
└─────────────────────────────────────┘
```

**Benefits:**
- Clear separation of concerns
- Testable business logic independent of HTTP layer
- Consistent error handling across layers

#### 2. Service Layer Pattern
All business logic resides in service modules (`app/services/`):
- `policy_service.py`: Policy lifecycle management
- `claim_service.py`: Claims processing and workflow
- `payment_service.py`: Payment operations and disbursements
- `vendor_service.py`: Vendor/claimant onboarding
- `auth_service.py`: Authentication and authorization
- `audit_service.py`: Audit trail logging

**Service responsibilities:**
- Business rules enforcement
- Data validation beyond schema validation
- Transaction management
- Audit logging
- Error handling with domain exceptions

#### 3. Repository Pattern (Implicit)
Services interact directly with SQLAlchemy async sessions:
- No separate repository layer for simplicity
- Database queries encapsulated within service functions
- Async/await throughout for non-blocking I/O

#### 4. Dependency Injection
FastAPI's `Depends()` mechanism provides:
- Database session per request: `Depends(get_session)`
- Current user extraction: `Depends(get_current_user_id)`
- Automatic resource cleanup

### Data Model Design

#### Core Entities

##### Policy
- **Primary Key**: `id` (integer)
- **Business Key**: `policy_number` (unique, indexed)
- **Search Fields**: Insured name, organization, location, type
- **Sensitive Data**: `ssn_tin` (encrypted at rest)
- **Relationships**: One-to-many with Claims
- **Audit**: `created_by`, `updated_by`, timestamps

##### Claim
- **Primary Key**: `id` (integer)
- **Business Key**: `claim_number` (unique, indexed)
- **Foreign Key**: `policy_id` → Policy
- **Status Workflow**: open → closed/paid/denied
- **Special Features**:
  - Claim-level policy data (JSON) for unverified policies
  - Injury incident details (JSON)
  - Subrogation tracking
  - Scheduled payments
- **Audit**: Full change tracking with user and timestamp

##### Payment
- **Primary Key**: `id` (integer)
- **Business Key**: `payment_number` (unique, indexed)
- **Foreign Keys**: `claim_id`, `policy_id`
- **Status Workflow**: pending → approved → issued (or void/reversed)
- **Payment Methods**: ACH, wire, card, Stripe, global payout
- **Sensitive Data**: `tax_id_number` (encrypted)
- **Features**:
  - Reserve line allocation (JSON)
  - Void/reversal with reason tracking
  - Reissue support
  - Tax reporting
- **Relationships**: One-to-many with PaymentDetail

##### PaymentDetail
- **Primary Key**: `id` (integer)
- **Foreign Key**: `payment_id` → Payment
- **Purpose**: Multiple payees per payment (joint payees)
- **Sensitive Data**: `banking_info` (JSON, encrypted)

##### User
- **Primary Key**: `id` (integer)
- **Authentication**: Email + bcrypt password hash
- **Roles**: RBAC with roles field (JSON)
- **Status**: Active/inactive flag

##### Vendor
- **Primary Key**: `id` (integer)
- **Purpose**: Vendor/claimant onboarding for payments
- **KYC**: Identity verification status
- **Payment Methods**: Multiple methods supported (JSON)

##### AuditLog
- **Purpose**: Immutable audit trail for compliance
- **Fields**: entity_type, entity_id, action, user_id, changes (JSON)
- **Indexed**: By entity, by user, by timestamp

### Security Architecture

#### Authentication & Authorization
1. **JWT-based authentication**:
   - Bearer token in `Authorization` header
   - Token includes `sub` (user_id) and `exp` (expiration)
   - Default expiration: 60 minutes (configurable)

2. **Password security**:
   - Bcrypt hashing with salt
   - Minimum complexity enforced at application level
   - Never logged or exposed in responses

3. **Role-based access control (RBAC)**:
   - User roles stored in User.roles (JSON array)
   - Middleware checks role before sensitive operations
   - Extensible for fine-grained permissions

#### Data Protection

##### Encryption at Rest
- **Fernet symmetric encryption** for sensitive fields:
  - SSN/TIN in Policy
  - Tax ID numbers in Payment
  - Banking information in PaymentDetail
- **Key derivation**: SHA-256 hash of `encryption_key` setting
- **Masked display**: SSN shown as `***-**-1234` in responses

##### PCI-DSS Compliance (Payment Data)
- Banking information never logged
- Encrypted in database
- Transmitted only over TLS in production
- Masked in API responses
- Audit trail for all payment operations

##### Audit Trail
- Every create/update/delete logged to `audit_logs` table
- User ID and timestamp captured
- Change details stored as JSON diff
- Immutable records (no updates/deletes allowed)

### Middleware Stack

#### 1. CorrelationIdMiddleware
- Extracts or generates correlation ID per request
- Propagates in `X-Correlation-Id` header
- Stored in context var for logging

#### 2. RequestLoggingMiddleware
- Logs every request: method, path, status, duration
- Includes correlation ID for distributed tracing
- Performance monitoring

#### 3. CORSMiddleware
- Configured origins from `cors_allowed_origins` setting
- Credentials support enabled
- Custom headers: `X-Correlation-Id`, `Authorization`

### Error Handling Strategy

#### Exception Hierarchy
```
AppException (base)
├── NotFoundException (404)
├── ConflictException (409)
├── ValidationException (400)
├── AuthException (401)
└── ForbiddenException (403)
```

#### Global Exception Handler
- Catches all `AppException` instances
- Returns standardized JSON response:
  ```json
  {
    "status": 404,
    "error": "NOT_FOUND",
    "message": "Policy with id 123 not found",
    "timestamp": "2026-03-01T10:30:00Z"
  }
  ```

#### FastAPI Validation Errors
- Caught and transformed to consistent format
- Field-level error details included

### API Design

#### RESTful Principles
- Resource-based URLs: `/policies`, `/claims`, `/payments`
- Standard HTTP methods: GET, POST, PUT, PATCH, DELETE
- Appropriate status codes: 200, 201, 404, 409, etc.

#### Pagination
- Standardized `PageResponse` wrapper:
  ```json
  {
    "items": [...],
    "total": 150,
    "page": 0,
    "size": 20,
    "pages": 8
  }
  ```

#### Search & Filtering
- GET endpoints accept query parameters
- Support for partial matching (ILIKE for text fields)
- Multiple filters combined with AND logic

#### OpenAPI Documentation
- Automatically generated at `/docs` (Swagger UI)
- Alternative at `/redoc` (ReDoc)
- Schema definitions from Pydantic models

### Integration Points

#### External Systems (Placeholders for Future)
The architecture supports integration with:
- **Stripe Connect**: Payment processing
- **Global Payouts**: International disbursements
- **Bank ACH/Wire**: Direct bank transfers
- **Xactimate/XactAnalysis**: Automated estimate ingestion
- **EDI 835/837**: Medical billing standards
- **Bill Review Services**: Medical claim review
- **Document Management**: Attachment storage

Integration pattern:
- Service layer methods call integration adapters
- Adapters handle external API communication
- Error handling and retry logic in adapters
- Async where possible for non-blocking calls

### Database Schema Strategy

#### Indexing
- **Primary keys**: Auto-incrementing integers
- **Business keys**: Unique indexes (policy_number, claim_number, etc.)
- **Foreign keys**: Indexed for join performance
- **Search fields**: Indexed (names, locations, statuses)

#### JSON Fields
Used for flexible data structures:
- **Policy**: coverage_types, coverage_limits, coverage_deductibles
- **Claim**: claim_level_policy_data, injury_incident_details, coding_information, carrier_involvement
- **Payment**: reserve_lines
- **PaymentDetail**: banking_info

**Rationale**: Avoid excessive table proliferation for semi-structured data that varies by policy type/state.

#### Audit Fields Pattern
Every entity has:
- `created_by` (user_id)
- `updated_by` (user_id, nullable)
- `created_at` (timestamp with timezone)
- `updated_at` (timestamp with timezone, auto-update)

### Performance Considerations

#### Async I/O
- All database operations use `async/await`
- Non-blocking request handling
- Scales well under concurrent load

#### Connection Pooling
- SQLAlchemy async engine with connection pool
- Configurable pool size for production

#### Query Optimization
- Eager loading where appropriate (future enhancement)
- Indexes on frequently queried fields
- Pagination limits result set size

#### Caching (Future)
- Redis for session storage
- Cache policy/claim lookups with short TTL
- Invalidate on updates

### Deployment Architecture

#### Development
- SQLite file-based database
- Uvicorn with `--reload` flag
- Debug mode enabled
- Minimal security (development secrets)

#### Production
- PostgreSQL database with connection pooling
- Uvicorn with multiple workers (Gunicorn)
- TLS/HTTPS required
- Environment-based secrets (AWS Secrets Manager, etc.)
- Health checks: `/health/live` (liveness), `/health/ready` (readiness)

### Configuration Management

#### Environment Variables
All configuration via `.env` file or environment variables:
- `DATABASE_URL`: Database connection string
- `JWT_SECRET`: Token signing secret (min 32 chars)
- `ENCRYPTION_KEY`: Fernet key for sensitive data encryption
- `CORS_ALLOWED_ORIGINS`: Comma-separated allowed origins
- `ENVIRONMENT`: dev/staging/production

#### Validation
- Pydantic Settings validates all configuration on startup
- Application fails fast if required settings missing
- No defaults for production secrets

### Testing Strategy

#### Unit Tests
- Test service layer functions in isolation
- Mock database sessions
- Focus on business logic correctness

#### Integration Tests
- Test API endpoints end-to-end
- Use test database (SQLite in-memory)
- Verify request/response contracts

#### Coverage Goals
- Minimum 80% code coverage
- 100% coverage for critical paths (payment processing, security)

### Compliance & Regulations

#### WCAG Accessibility
- API design supports accessible frontend clients
- Clear, descriptive error messages
- Consistent response formats

#### PCI-DSS
- Payment data encrypted at rest and in transit
- No logging of sensitive payment information
- Access controls on payment operations
- Audit trail for all payment actions

#### Data Retention
- Audit logs retained indefinitely
- Policy/claim data retained per regulatory requirements
- Soft delete pattern (future enhancement)

### Future Enhancements

#### Phase 2 (Planned)
- Redis caching layer
- WebSocket support for real-time updates
- Background job processing (Celery)
- Document attachment storage (S3)
- Full-text search (Elasticsearch)

#### Phase 3 (Future)
- GraphQL API option
- Multi-tenancy support
- Advanced analytics and reporting
- Machine learning for fraud detection

### Conclusion

This architecture provides a solid foundation for a comprehensive insurance platform with:
- **Security**: Encryption, authentication, audit trail
- **Scalability**: Async I/O, connection pooling, horizontal scaling
- **Maintainability**: Layered architecture, clear patterns, comprehensive tests
- **Extensibility**: Integration-ready design, flexible data model

The implementation follows industry best practices and is production-ready with appropriate configuration and infrastructure.
