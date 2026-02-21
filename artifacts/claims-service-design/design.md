# Claims Service Platform - Technical Design

## Approach

### High-Level Architecture
This design implements a **layered architecture** with clear separation of concerns:

1. **Presentation Layer**: React TypeScript frontend with responsive design
2. **API Layer**: FastAPI REST endpoints with OpenAPI documentation
3. **Business Logic Layer**: Service classes handling domain rules and workflows
4. **Data Access Layer**: SQLAlchemy ORM with encrypted field support
5. **Infrastructure Layer**: PostgreSQL database, external integrations

### Key Architectural Decisions

**Database Design**: PostgreSQL with field-level encryption for PII (SSN/TIN) and payment data. Separate audit table for all operations. Claims can override policy data without affecting original policy records.

**Authentication**: JWT-based authentication with role-based access control (RBAC). Tokens include user ID and roles for authorization decisions.

**Security**: End-to-end encryption for sensitive data, input validation at API boundaries, audit logging for all operations, PCI-DSS compliant payment processing.

**Integration Strategy**: Service layer abstractions for external integrations (Stripe, ACH, EDI) with circuit breaker pattern and retry logic.

## Detailed Changes

### Backend Infrastructure

**backend/main.py**
- FastAPI application setup with CORS middleware
- Mount all API routers (/api/policies, /api/claims, /api/payments, /api/auth)
- Global exception handlers and middleware for audit logging
- OpenAPI documentation configuration

**backend/app/core/config.py**
- Environment-based configuration using Pydantic settings
- Database connection strings, JWT secrets, encryption keys
- External service configurations (Stripe, payment processors)
- Performance settings (connection pools, timeouts)

**backend/app/core/database.py**
- SQLAlchemy engine with connection pooling
- Session management with proper cleanup
- Database migration support via Alembic
- Encrypted field type definitions for PII

**backend/app/core/security.py**
- JWT token creation and validation
- Password hashing using bcrypt
- Role-based access decorators
- Field-level encryption/decryption utilities

### Data Models

**backend/app/models/policy.py**
- Policy entity with encrypted SSN/TIN fields
- Vehicle details (year, make, model, VIN)
- Location details (address, city, state, zip)
- Coverage details (types, limits, deductibles)
- Relationships to claims and audit records
- Search indexes on policy number, names, dates

**backend/app/models/claim.py**
- Claims entity with foreign key to policy
- Claim-level policy override fields (separate from original policy)
- Status tracking (Open, Closed, Paid, Denied)
- Date of loss, claim number, claim type
- Relationships to payments and audit records
- Visual indicator flag for claim-level policy data usage

**backend/app/models/payment.py**
- Payment entity with encrypted payment method details
- Reserve line allocation tracking
- Payment lifecycle status (Created, Pending, Completed, Failed, Voided)
- Tax reporting fields and withholding amounts
- Joint payee support and document attachments
- Relationships to claims and audit records

**backend/app/models/user.py**
- User authentication with hashed passwords
- Role definitions (Admin, Adjuster, Processor, Viewer)
- User profile information and preferences
- Session tracking and last login timestamps

**backend/app/models/audit.py**
- Comprehensive audit trail for all operations
- User ID, timestamp, action type, table name
- Before/after data snapshots for changes
- IP address and user agent tracking

### API Schemas

**backend/app/schemas/policy.py**
- PolicyCreate: Input validation for new policies
- PolicyUpdate: Partial update schema with optional fields
- PolicyResponse: Output schema with masked PII fields
- PolicySearchRequest: Complex search criteria validation
- PolicySearchResponse: Paginated results with metadata

**backend/app/schemas/claim.py**
- ClaimCreate: New claim with policy relationship validation
- ClaimUpdate: Status changes and claim-level policy overrides
- ClaimResponse: Full claim details with policy information
- ClaimHistoryResponse: List of claims with sorting/filtering

**backend/app/schemas/payment.py**
- PaymentCreate: Payment method validation and amount constraints
- PaymentUpdate: Status changes and allocation modifications
- PaymentResponse: Payment details with sensitive data masking
- PaymentMethodSchema: Different payment types (ACH, Wire, Card)

### Business Logic Services

**backend/app/services/policy_service.py**
- Complex policy search with multiple criteria (exact/partial matching)
- PII masking for SSN/TIN display
- Policy CRUD operations with audit logging
- Data validation and business rule enforcement
- Integration with external policy systems

**backend/app/services/claims_service.py**
- Claims-to-policy relationship management
- Claim-level policy editing with change tracking
- Claims history with status filtering and sorting
- Workflow management (status transitions, approvals)
- Integration with subrogation systems

**backend/app/services/payment_service.py**
- Payment lifecycle management (create, void, reverse, reissue)
- Reserve line allocation across multiple lines
- Tax compliance and withholding calculations
- Integration with Stripe Connect, ACH, and wire systems
- PCI-DSS compliant payment processing

**backend/app/services/audit_service.py**
- Automatic audit record creation for all CRUD operations
- Data change tracking with before/after snapshots
- User context capture and session tracking
- Audit query and reporting capabilities

### API Endpoints

**backend/app/api/policies.py**
- `GET /api/policies/search` - Complex policy search with pagination
- `GET /api/policies/{policy_id}` - Policy details with claims history
- `POST /api/policies` - Create new policy with validation
- `PUT /api/policies/{policy_id}` - Update policy with audit trail
- `GET /api/policies/{policy_id}/audit` - Policy audit history

**backend/app/api/claims.py**
- `GET /api/claims` - Claims list with filtering and sorting
- `GET /api/claims/{claim_id}` - Claim details with policy information
- `POST /api/claims` - Create new claim with policy linking
- `PUT /api/claims/{claim_id}` - Update claim with policy overrides
- `GET /api/policies/{policy_id}/claims` - Claims history for policy

**backend/app/api/payments.py**
- `GET /api/payments` - Payment list with status filtering
- `GET /api/payments/{payment_id}` - Payment details and lifecycle
- `POST /api/payments` - Create payment with validation
- `PUT /api/payments/{payment_id}` - Update payment status/allocation
- `POST /api/payments/{payment_id}/void` - Void payment transaction

### Frontend Application

**frontend/src/App.tsx**
- React Router setup with protected routes
- Authentication wrapper component
- Global error boundary for payment operations
- Layout component with navigation and user context

**frontend/src/pages/PolicySearch.tsx**
- Multi-criteria search form with reset functionality
- Results table with sorting and pagination
- WCAG compliant design with keyboard navigation
- Loading states and error handling

**frontend/src/pages/PolicyDetails.tsx**
- Policy information display with PII masking
- Claims history section with status filtering
- Edit mode for policy updates with validation
- Audit trail display with change tracking

**frontend/src/pages/ClaimsList.tsx**
- Claims list with date sorting (most recent first)
- Status filtering (Open, Closed, Paid, Denied)
- Visual indicators for claim-level policy data
- Quick actions for status changes

**frontend/src/pages/PaymentProcessing.tsx**
- Payment creation forms for different methods
- Reserve line allocation interface
- Tax compliance fields and withholding
- Payment lifecycle tracking and status updates

### Utility Components

**frontend/src/components/SearchForm.tsx**
- Reusable search component with field validation
- Support for exact and partial matching modes
- Responsive design with mobile optimization
- Accessibility features and keyboard shortcuts

**frontend/src/components/DataTable.tsx**
- Generic sortable/filterable table component
- Pagination support with configurable page sizes
- Column customization and data formatting
- Export functionality for reporting

**frontend/src/services/api.ts**
- Typed HTTP client with automatic authentication headers
- Request/response interceptors for error handling
- Retry logic for transient failures
- Request caching for performance optimization

## Interfaces

### Core API Contracts

```typescript
// Policy Search API
POST /api/policies/search
{
  "policy_number"?: string,
  "insured_first_name"?: string,
  "insured_last_name"?: string,
  "policy_type"?: string,
  "loss_date_from"?: string,
  "loss_date_to"?: string,
  "policy_city"?: string,
  "policy_state"?: string,
  "policy_zip"?: string,
  "ssn_tin"?: string,
  "organization_name"?: string,
  "search_type": "exact" | "partial"
}

// Claims History API
GET /api/policies/{policy_id}/claims?status=open&sort_by=loss_date&order=desc

// Payment Creation API
POST /api/payments
{
  "claim_id": string,
  "amount": number,
  "payment_method": "ACH" | "WIRE" | "CARD" | "STRIPE",
  "payee_info": { ... },
  "reserve_allocations": [{ "line": string, "amount": number }],
  "tax_withholding": number,
  "is_tax_reportable": boolean
}
```

### Database Schema Key Relationships

```sql
-- Policy to Claims (One-to-Many)
claims.policy_id -> policies.id

-- Claims to Payments (One-to-Many)
payments.claim_id -> claims.id

-- All tables to Audit (Many-to-One)
audit_logs.table_name + audit_logs.record_id -> {table}.id
```

### Encryption Interface

```python
# Field-level encryption for PII
class EncryptedField(TypeDecorator):
    def process_bind_param(self, value, dialect):
        return encrypt_field(value) if value else None

    def process_result_value(self, value, dialect):
        return decrypt_field(value) if value else None

# Usage in models
ssn = Column(EncryptedField(String(11)))
```

## Trade-offs

### Database Design Choices

**PostgreSQL over NoSQL**: Chose PostgreSQL for ACID compliance and complex relational queries required for policy/claims/payments relationships. Trade-off: potentially slower for simple reads but ensures data consistency for financial transactions.

**Field-level encryption**: Implemented at application layer vs database level for better control and key management. Trade-off: additional complexity but better security granularity.

**Separate audit table**: Single audit table vs per-table audit logs. Chosen for unified audit queries and easier compliance reporting. Trade-off: potential performance impact for high-volume operations.

### Frontend Architecture Choices

**React Context vs Redux**: Using React Context for authentication state due to simpler setup and smaller state tree. Trade-off: less powerful dev tools but adequate for application scope.

**Component co-location**: Keeping related components, hooks, and services together vs strict layer separation. Trade-off: potentially larger bundle chunks but better developer experience.

### Security Implementation

**JWT vs Session-based auth**: JWT for stateless authentication supporting multiple frontend clients. Trade-off: token revocation complexity but better scalability.

**Client-side PII masking**: Masking sensitive data on backend before sending to frontend. Trade-off: requires more API calls for full data but prevents accidental exposure.

### Integration Strategy

**Service layer abstraction**: Wrapping external APIs (Stripe, payment processors) in service classes vs direct integration. Trade-off: additional abstraction layer but easier testing and provider switching.

## Open Questions

### Implementation Decisions for Development Agent

1. **Database Migration Strategy**: Should we use Alembic auto-generation or hand-written migrations for the initial schema? Recommend hand-written for better control over encryption setup.

2. **Caching Strategy**: Which operations need caching (policy searches, user sessions)? Consider Redis for session storage and policy search result caching.

3. **Error Handling Granularity**: How detailed should error messages be for different user roles? Recommend role-based error detail levels for security.

4. **Payment Processor Priority**: If multiple payment methods are available, what's the fallback order? Suggest configuration-driven priority with cost optimization.

5. **Audit Data Retention**: How long should audit logs be retained and should they be archived? Consider regulatory requirements and storage costs.

6. **Search Performance**: Should policy search use full-text indexing or composite indexes? Recommend composite indexes initially with full-text as optimization.

7. **File Upload Strategy**: For document attachments, use local storage, S3, or database BLOBs? Recommend S3 with encryption for scalability.

8. **Real-time Updates**: Should payment status changes trigger real-time notifications to frontend? Consider WebSocket integration for critical updates.

9. **API Rate Limiting**: What rate limits should be applied to different endpoints? Recommend stricter limits on payment operations.

10. **Development Environment**: Should docker-compose include external service mocks (Stripe test mode, mock ACH)? Recommend test mode integrations for development.

### Configuration Considerations

The implementation agent should configure:
- JWT token expiration times (recommend 15 min access, 7 day refresh)
- Database connection pool sizes based on expected load
- Encryption key rotation strategy
- External service timeout and retry settings
- Audit log retention and archival policies
- Search result pagination sizes
- File upload size limits and allowed types