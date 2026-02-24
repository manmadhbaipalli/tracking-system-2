# Integrated Policy, Claims, and Payments Platform - Requirements Document

## User Stories

### Authentication & Access Control

#### US-001: User Authentication
**As a** system user
**I want to** authenticate with my credentials
**So that** I can access the platform with appropriate role-based permissions

**Acceptance Criteria:**
- AC-001.1: System accepts email and password for authentication
- AC-001.2: System validates credentials against stored user records
- AC-001.3: System returns JWT access token on successful authentication
- AC-001.4: System enforces role-based access control (Admin, Agent, Adjuster, Viewer)
- AC-001.5: System logs all authentication attempts with user ID and timestamp
- AC-001.6: System tracks user sessions for audit purposes

**Error Scenarios:**
- E-001.1: Invalid credentials → 401 with message "Invalid email or password"
- E-001.2: Account disabled → 403 with message "Account is disabled"
- E-001.3: Too many failed attempts → 429 with message "Account temporarily locked"

#### US-002: Role-Based Access
**As a** system administrator
**I want to** control user access based on roles
**So that** users can only perform actions appropriate to their role

**Acceptance Criteria:**
- AC-002.1: System enforces role permissions on all endpoints
- AC-002.2: Admin role has full access to all modules
- AC-002.3: Agent role has access to policies, claims, and payments within their scope
- AC-002.4: Adjuster role has access to claims processing and payments
- AC-002.5: Viewer role has read-only access to assigned records
- AC-002.6: System logs all access attempts and permission checks

**Error Scenarios:**
- E-002.1: Insufficient permissions → 403 with message "Insufficient permissions for this action"
- E-002.2: Invalid role → 403 with message "Invalid user role"

### Policy Management

#### US-003: Policy Search
**As a** system user
**I want to** search for policies using multiple criteria
**So that** I can quickly find relevant policy information

**Acceptance Criteria:**
- AC-003.1: System accepts search by Policy Number, Insured First Name, Insured Last Name
- AC-003.2: System accepts search by Policy Type, Loss Date, Policy City, Policy State, Policy Zip
- AC-003.3: System accepts search by SSN/TIN and Organizational Name
- AC-003.4: System supports both exact and partial matches for names, policy numbers, and addresses
- AC-003.5: System returns results within 3 seconds for any search criteria combination
- AC-003.6: System displays results in paginated format (default 20, max 100 per page)
- AC-003.7: System allows users to reset all search criteria to default/empty values
- AC-003.8: System masks SSN/TIN in search results (showing only last 4 digits)

**Error Scenarios:**
- E-003.1: No matching policies found → Display "No matching policies found"
- E-003.2: Search timeout → Display "Search is taking longer than expected. Please try again"
- E-003.3: Invalid search criteria → 400 with field-specific validation errors
- E-003.4: System unavailable → Display "System is currently unavailable"

#### US-004: Policy Details View
**As a** system user
**I want to** view comprehensive policy details
**So that** I can access all relevant policy information

**Acceptance Criteria:**
- AC-004.1: System displays Insured Name, Policy Number, Policy Type, Effective Date, Expiration Date
- AC-004.2: System displays Policy Status, Vehicle Details (Year, Make, Model, VIN)
- AC-004.3: System displays Location Details (Address, City, State, Zip)
- AC-004.4: System displays Coverage Details (Types, Limits, Deductibles)
- AC-004.5: System loads policy details within 5 seconds
- AC-004.6: System masks SSN/TIN according to security policies (show last 4 digits only)
- AC-004.7: System displays are WCAG compliant for accessibility
- AC-004.8: System logs all policy detail access with user ID and timestamp

**Error Scenarios:**
- E-004.1: Policy not found → 404 with message "Policy not found"
- E-004.2: Unable to retrieve details → Display "Unable to retrieve details. Please try again later"
- E-004.3: Access denied → 403 with message "Access denied for this policy"

#### US-005: Policy Creation
**As an** authorized user
**I want to** create new policies
**So that** I can manage policy portfolio

**Acceptance Criteria:**
- AC-005.1: System accepts all required policy fields (Insured Name, Policy Number, Type, Dates)
- AC-005.2: System validates policy number uniqueness
- AC-005.3: System validates effective date is not in the past (unless admin override)
- AC-005.4: System stores vehicle details with VIN validation
- AC-005.5: System stores location details with address validation
- AC-005.6: System stores coverage details with limits and deductibles
- AC-005.7: System encrypts and masks SSN/TIN data
- AC-005.8: System creates audit log entry for policy creation

**Error Scenarios:**
- E-005.1: Duplicate policy number → 409 with message "Policy number already exists"
- E-005.2: Invalid effective date → 400 with message "Effective date cannot be in the past"
- E-005.3: Missing required fields → 400 with field-specific validation errors
- E-005.4: Invalid VIN format → 400 with message "Invalid VIN format"

#### US-006: Policy Update
**As an** authorized user
**I want to** update existing policies
**So that** I can maintain accurate policy information

**Acceptance Criteria:**
- AC-006.1: System allows updating all modifiable policy fields
- AC-006.2: System validates changes against business rules
- AC-006.3: System maintains audit trail of all changes with before/after values
- AC-006.4: System updates policy effective immediately unless future-dated
- AC-006.5: System notifies related claims of policy changes
- AC-006.6: System logs update action with user ID, timestamp, and changed fields

**Error Scenarios:**
- E-006.1: Policy not found → 404 with message "Policy not found"
- E-006.2: Invalid update data → 400 with field-specific validation errors
- E-006.3: Concurrent update conflict → 409 with message "Policy was modified by another user"
- E-006.4: Business rule violation → 400 with specific rule violation message

### Claims Management

#### US-007: Claim Creation
**As an** authorized user
**I want to** create claims linked to policies
**So that** I can process insurance claims

**Acceptance Criteria:**
- AC-007.1: System requires valid policy ID for claim creation
- AC-007.2: System accepts claim details (Date of Loss, Claim Type, Description)
- AC-007.3: System generates unique claim number automatically
- AC-007.4: System sets initial claim status to "Open"
- AC-007.5: System allows injury incident details and coding information
- AC-007.6: System supports carrier involvement information
- AC-007.7: System creates audit log entry for claim creation
- AC-007.8: System links claim to policy with proper relationships

**Error Scenarios:**
- E-007.1: Invalid policy ID → 400 with message "Invalid policy reference"
- E-007.2: Policy not found → 404 with message "Referenced policy not found"
- E-007.3: Missing required claim data → 400 with field-specific validation errors
- E-007.4: Date of Loss in future → 400 with message "Date of Loss cannot be in the future"

#### US-008: Claim History View
**As a** system user
**I want to** view claim history for a policy
**So that** I can review past claims

**Acceptance Criteria:**
- AC-008.1: System displays list of claims associated with the policy
- AC-008.2: System shows Claim Number, Date of Loss, Claim Status for each claim
- AC-008.3: System sorts claims by Date of Loss (most recent first)
- AC-008.4: System allows filtering by Claim Status (Open, Closed, Paid, Denied)
- AC-008.5: System loads claim history within 5 seconds
- AC-008.6: System displays "No prior claims exist for this policy" when no claims found
- AC-008.7: System logs claim history access with user ID and timestamp

**Error Scenarios:**
- E-008.1: Policy not found → 404 with message "Policy not found"
- E-008.2: Unable to retrieve claims → Display "Unable to retrieve claim history. Please try again later"
- E-008.3: Access denied → 403 with message "Access denied for claim history"

#### US-009: Claim-Level Policy Information
**As an** adjuster
**I want to** add/edit policy information at claim level when policy is unverified
**So that** I can proceed with claims processing while maintaining data integrity

**Acceptance Criteria:**
- AC-009.1: System allows editing policy information at claim level when policy status is "unverified"
- AC-009.2: System tracks claim-level policy changes separately from original policy data
- AC-009.3: System displays visual indicator when claim-level policy information is being used
- AC-009.4: System maintains original policy data unchanged
- AC-009.5: System creates separate audit log for claim-level policy changes
- AC-009.6: System tracks user ID and timestamp for all claim-level policy modifications

**Error Scenarios:**
- E-009.1: Policy verified → 400 with message "Cannot modify policy information for verified policy"
- E-009.2: Unable to save changes → Display "Unable to save claim-level policy data. Please try again later"
- E-009.3: Invalid policy data → 400 with field-specific validation errors

#### US-010: Claim Status Management
**As an** adjuster
**I want to** update claim status and manage workflow
**So that** I can track claim progress through processing stages

**Acceptance Criteria:**
- AC-010.1: System supports claim statuses: Open, In Progress, Closed, Paid, Denied
- AC-010.2: System validates status transitions according to business rules
- AC-010.3: System requires reason/notes for status changes
- AC-010.4: System tracks status change history with timestamps
- AC-010.5: System supports referral to subrogation
- AC-010.6: System manages scheduled payments (applicability, type, total amount, balance, current due)
- AC-010.7: System identifies recipients for scheduled payments

**Error Scenarios:**
- E-010.1: Invalid status transition → 400 with message "Invalid status transition from [current] to [new]"
- E-010.2: Missing required reason → 400 with message "Reason required for status change"
- E-010.3: Claim not found → 404 with message "Claim not found"

### Payments & Disbursements

#### US-011: Payment Method Setup
**As a** system administrator
**I want to** onboard vendors and claimants with payment methods
**So that** they can receive payments securely

**Acceptance Criteria:**
- AC-011.1: System supports ACH, wire, credit/debit card, Stripe Connect, global payouts
- AC-011.2: System performs KYC/Identity verification for payment method setup
- AC-011.3: System securely stores payment method details with encryption
- AC-011.4: System validates banking details for ACH and wire transfers
- AC-011.5: System captures tax ID numbers for payees when required
- AC-011.6: System maintains audit trail of payment method setup and changes

**Error Scenarios:**
- E-011.1: KYC verification failed → 400 with message "Identity verification failed"
- E-011.2: Invalid banking details → 400 with message "Invalid banking information"
- E-011.3: Duplicate payment method → 409 with message "Payment method already exists"
- E-011.4: Missing required tax ID → 400 with message "Tax ID required for this payee type"

#### US-012: Payment Creation
**As an** authorized user
**I want to** create payments linked to claims
**So that** I can disburse funds to appropriate recipients

**Acceptance Criteria:**
- AC-012.1: System requires valid claim ID for payment creation
- AC-012.2: System supports positive, negative, and zero dollar amounts
- AC-012.3: System allows allocation across multiple reserve lines
- AC-012.4: System supports designation as eroding or non-eroding against reserves
- AC-012.5: System manages multiple payees per payment transaction
- AC-012.6: System handles joint payees and payment portions
- AC-012.7: System supports deductions and withholdings
- AC-012.8: System allows document attachment to payments
- AC-012.9: System processes payment within 5 seconds including external validations

**Error Scenarios:**
- E-012.1: Invalid claim ID → 400 with message "Invalid claim reference"
- E-012.2: Insufficient reserve balance → 400 with message "Insufficient reserve balance"
- E-012.3: Invalid payment amount → 400 with message "Invalid payment amount"
- E-012.4: Missing required payee information → 400 with field-specific validation errors

#### US-013: Payment Lifecycle Management
**As an** authorized user
**I want to** manage the complete payment lifecycle
**So that** I can handle voids, reversals, and reissues

**Acceptance Criteria:**
- AC-013.1: System supports payment void operations with reason tracking
- AC-013.2: System supports payment reversals with impact on reserves
- AC-013.3: System supports payment reissues with new payment method
- AC-013.4: System maintains complete audit trail of all lifecycle changes
- AC-013.5: System updates reserve balances automatically for all operations
- AC-013.6: System prevents operations on already processed payments
- AC-013.7: System tracks relationships between original and modified payments

**Error Scenarios:**
- E-013.1: Payment already processed → 400 with message "Cannot modify processed payment"
- E-013.2: Invalid operation → 400 with message "Operation not allowed for current payment status"
- E-013.3: Missing void/reversal reason → 400 with message "Reason required for payment modification"

#### US-014: Tax Reporting and Compliance
**As a** system administrator
**I want to** manage tax reporting for payments
**So that** I can ensure compliance with tax regulations

**Acceptance Criteria:**
- AC-014.1: System allows designation of payments as tax reportable
- AC-014.2: System captures and validates tax ID numbers for reportable payments
- AC-014.3: System calculates and withholds income tax when required
- AC-014.4: System generates tax reporting documents (1099s, etc.)
- AC-014.5: System maintains tax year reporting by payee
- AC-014.6: System ensures PCI-DSS compliance for all tax-related data

**Error Scenarios:**
- E-014.1: Missing tax ID for reportable payment → 400 with message "Tax ID required for reportable payment"
- E-014.2: Invalid tax ID format → 400 with message "Invalid tax ID format"
- E-014.3: Tax calculation error → 500 with message "Unable to calculate tax withholding"

#### US-015: EDI and Medical Payments
**As a** medical payment processor
**I want to** handle EDI/EOB-style remittances
**So that** I can process medical provider payments efficiently

**Acceptance Criteria:**
- AC-015.1: System supports EDI 835/837 format processing
- AC-015.2: System maps CPT/ICD codes for medical procedures
- AC-015.3: System handles adjustments and denials in remittances
- AC-015.4: System integrates with bill review vendors
- AC-015.5: System generates compliant remittance advice
- AC-015.6: System tracks medical payment status and follow-ups

**Error Scenarios:**
- E-015.1: Invalid EDI format → 400 with message "Invalid EDI format"
- E-015.2: Missing CPT/ICD codes → 400 with message "Medical codes required"
- E-015.3: Bill review integration failure → 500 with message "Bill review service unavailable"

### Negotiation & Settlement Management

#### US-016: Settlement Management
**As a** claims adjuster
**I want to** manage negotiations and settlements
**So that** I can resolve claims effectively

**Acceptance Criteria:**
- AC-016.1: System tracks negotiation history with all parties
- AC-016.2: System manages coverage opinion requests
- AC-016.3: System supports settlement plan creation and tracking
- AC-016.4: System handles settlement approvals and authorization levels
- AC-016.5: System integrates settlement amounts with payment processing
- AC-016.6: System maintains audit trail of all settlement activities

**Error Scenarios:**
- E-016.1: Unauthorized settlement amount → 403 with message "Settlement amount exceeds authorization level"
- E-016.2: Invalid settlement terms → 400 with message "Invalid settlement terms"
- E-016.3: Missing required approvals → 400 with message "Settlement requires additional approvals"

### Integration and External Systems

#### US-017: External System Integration
**As a** system administrator
**I want to** integrate with external systems
**So that** the platform can leverage existing infrastructure

**Acceptance Criteria:**
- AC-017.1: System integrates with Stripe Connect for payment processing
- AC-017.2: System integrates with Global Payouts for international payments
- AC-017.3: System integrates with Bank ACH/Wire services
- AC-017.4: System integrates with Xactimate/XactAnalysis for estimates
- AC-017.5: System integrates with Document Management systems
- AC-017.6: System supports error handling and retry logic for all integrations
- AC-017.7: System captures and reuses Other Carrier Information across functions

**Error Scenarios:**
- E-017.1: External service unavailable → 503 with message "External service temporarily unavailable"
- E-017.2: Integration authentication failed → 401 with message "External service authentication failed"
- E-017.3: Data format mismatch → 400 with message "Data format incompatible with external service"

## Business Rules

**BR-001: Policy Number Uniqueness** — No two active policies can have the same policy number within the system
**BR-002: SSN/TIN Masking** — SSN/TIN must be masked showing only last 4 digits in all user interfaces and logs
**BR-003: Claim-Policy Relationship** — Every claim must be linked to a valid policy; claims cannot exist without policy association
**BR-004: Payment-Claim Relationship** — Every payment must be linked to a valid claim; payments cannot exist without claim association
**BR-005: Audit Trail Requirement** — All create, update, delete operations must be logged with user ID, timestamp, and changed values
**BR-006: Role-Based Data Access** — Users can only access policies, claims, and payments within their assigned scope and role permissions
**BR-007: Date Validation** — Date of Loss cannot be in the future; Policy Effective Date validation based on user role
**BR-008: Reserve Balance Validation** — Payments cannot exceed available reserve balances unless specifically authorized
**BR-009: Payment Method Verification** — All payment methods must pass KYC/Identity verification before use
**BR-010: Tax Reporting Compliance** — Tax ID required for all reportable payments above threshold amounts
**BR-011: Claim Status Workflow** — Claim status changes must follow defined workflow rules (Open → In Progress → Closed/Paid/Denied)
**BR-012: Data Encryption** — All sensitive data (SSN/TIN, payment information, PII) must be encrypted at rest and in transit
**BR-013: Concurrent Update Prevention** — System must prevent concurrent updates to the same record with optimistic locking
**BR-014: Search Performance** — Policy searches must complete within 3 seconds regardless of search criteria complexity
**BR-015: Payment Processing Time** — Payment processing including external validations must complete within 5 seconds

## Non-Functional Requirements

### Performance
- API response time: < 500ms for 95th percentile of requests
- Policy search results: < 3 seconds for any search criteria combination
- Policy details and claim history: < 5 seconds load time
- Payment processing: < 5 seconds including external validations
- Database queries: < 100ms for simple queries, < 1 second for complex joins
- Pagination: default 20 items, maximum 100 items per page
- Concurrent user sessions: support 100+ concurrent users without performance degradation

### Security
- Authentication: JWT tokens with configurable expiration (default 8 hours)
- Authorization: Role-based access control (RBAC) with granular permissions
- Password storage: BCrypt hashing with minimum 12 rounds
- Data masking: SSN/TIN showing only last 4 digits in UI and logs
- Data encryption: AES-256 encryption for sensitive data at rest
- Transport security: TLS 1.3 for all data in transit
- PCI-DSS compliance: Full compliance for payment card data handling
- Input validation: Comprehensive validation on all API endpoints
- CORS: Configured with specific origins, no wildcard in production
- Session management: Stateless JWT-based authentication
- Audit logging: All sensitive operations logged with user context
- Data retention: Configurable retention policies for audit logs

### Reliability
- Uptime: 99.9% availability during business hours
- Health checks: Liveness and readiness endpoints for monitoring
- Error handling: Graceful error handling with no stack traces in API responses
- Database connectivity: Connection pooling with automatic retry
- External integration resilience: Circuit breaker pattern with retry logic
- Data backup: Automated daily backups with point-in-time recovery
- Failover: Automated failover for database connections
- Transaction integrity: ACID compliance for all financial transactions

### Observability
- Structured logging: JSON format with correlation IDs
- Request/response logging: All API calls logged (excluding sensitive data)
- Performance metrics: Response times, throughput, error rates
- Business metrics: Claims processed, payments made, policy searches
- Health monitoring: Database connection health, external service status
- Alert system: Automated alerts for system errors and performance degradation
- Audit trail: Complete audit logs for all data modifications
- User activity tracking: Login patterns, feature usage analytics

### Scalability
- Stateless design: No server-side session storage
- Database optimization: Proper indexing for search performance
- Connection pooling: Efficient database connection management
- Pagination: All list endpoints support pagination
- Caching strategy: Redis caching for frequently accessed data
- Load balancing: Support for horizontal scaling
- Resource efficiency: Memory and CPU optimization for concurrent users

### Configuration
- Environment variables: All configuration via environment variables
- Environment profiles: Development, staging, production configurations
- Feature flags: Configurable feature toggles for gradual rollouts
- External service URLs: Configurable endpoints for all integrations
- Business rules: Configurable thresholds and limits
- Security settings: Configurable JWT expiration, password policies
- Integration timeouts: Configurable timeout values for external services
- Audit settings: Configurable audit log retention and detail levels

## Domain Model

### User
- id: integer (PK, auto-generated)
- email: string (unique, required, max 255)
- password_hash: string (required, max 255, BCrypt)
- first_name: string (required, max 100)
- last_name: string (required, max 100)
- role: enum [ADMIN, AGENT, ADJUSTER, VIEWER] (required, default: VIEWER)
- active: boolean (default: true)
- last_login: datetime (nullable)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

**Relationships:**
- User 1:N AuditLog (one user creates many audit entries)

### Policy
- id: integer (PK, auto-generated)
- policy_number: string (unique, required, max 50)
- insured_first_name: string (required, max 100)
- insured_last_name: string (required, max 100)
- organizational_name: string (optional, max 255)
- policy_type: string (required, max 50)
- effective_date: date (required)
- expiration_date: date (required)
- status: enum [ACTIVE, INACTIVE, CANCELLED, EXPIRED] (required, default: ACTIVE)
- ssn_tin: string (encrypted, max 20)
- ssn_tin_masked: string (computed, shows last 4 digits only)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

**Relationships:**
- Policy 1:N Claim (one policy has many claims)
- Policy 1:N Vehicle (one policy covers many vehicles)
- Policy 1:N Location (one policy has many locations)
- Policy 1:N Coverage (one policy has many coverages)

### Vehicle
- id: integer (PK, auto-generated)
- policy_id: integer (FK to Policy, required)
- year: integer (required, min 1900, max current_year + 1)
- make: string (required, max 50)
- model: string (required, max 50)
- vin: string (required, unique, exactly 17 chars)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

### Location
- id: integer (PK, auto-generated)
- policy_id: integer (FK to Policy, required)
- address: string (required, max 255)
- city: string (required, max 100)
- state: string (required, exactly 2 chars)
- zip_code: string (required, max 10)
- country: string (default: 'US', max 2)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

### Coverage
- id: integer (PK, auto-generated)
- policy_id: integer (FK to Policy, required)
- coverage_type: string (required, max 100)
- limit_amount: decimal(15,2) (required, min 0)
- deductible_amount: decimal(15,2) (required, min 0)
- premium_amount: decimal(15,2) (required, min 0)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

### Claim
- id: integer (PK, auto-generated)
- claim_number: string (unique, auto-generated, required, max 50)
- policy_id: integer (FK to Policy, required)
- date_of_loss: date (required)
- claim_type: string (required, max 100)
- description: text (required)
- status: enum [OPEN, IN_PROGRESS, CLOSED, PAID, DENIED] (required, default: OPEN)
- total_incurred: decimal(15,2) (default: 0)
- total_paid: decimal(15,2) (default: 0)
- total_reserve: decimal(15,2) (default: 0)
- subrogation_referral: boolean (default: false)
- injury_incident: boolean (default: false)
- carrier_involved: boolean (default: false)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

**Relationships:**
- Claim N:1 Policy (many claims belong to one policy)
- Claim 1:N Payment (one claim has many payments)
- Claim 1:N ClaimPolicyOverride (one claim can have policy overrides)
- Claim 1:N Reserve (one claim has multiple reserve lines)
- Claim 1:N Settlement (one claim can have multiple settlements)

### ClaimPolicyOverride
- id: integer (PK, auto-generated)
- claim_id: integer (FK to Claim, required)
- field_name: string (required, max 100)
- original_value: text (nullable)
- override_value: text (required)
- reason: text (required)
- created_by: integer (FK to User, required)
- created_at: datetime (auto-set, required)

### Reserve
- id: integer (PK, auto-generated)
- claim_id: integer (FK to Claim, required)
- reserve_type: string (required, max 100)
- initial_amount: decimal(15,2) (required)
- current_balance: decimal(15,2) (required)
- paid_amount: decimal(15,2) (default: 0)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

### Payment
- id: integer (PK, auto-generated)
- payment_number: string (unique, auto-generated, required, max 50)
- claim_id: integer (FK to Claim, required)
- payment_type: enum [CHECK, ACH, WIRE, CREDIT_CARD, STRIPE, GLOBAL_PAYOUT] (required)
- total_amount: decimal(15,2) (required)
- net_amount: decimal(15,2) (required)
- status: enum [PENDING, PROCESSING, COMPLETED, FAILED, VOIDED, REVERSED] (required, default: PENDING)
- is_tax_reportable: boolean (default: false)
- tax_withholding: decimal(15,2) (default: 0)
- eroding_type: enum [ERODING, NON_ERODING] (required, default: ERODING)
- void_reason: text (nullable)
- processed_at: datetime (nullable)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

**Relationships:**
- Payment N:1 Claim (many payments belong to one claim)
- Payment 1:N PaymentPayee (one payment can have multiple payees)
- Payment 1:N PaymentReserveAllocation (payment allocated across reserves)
- Payment 1:N PaymentDocument (payment can have attached documents)

### Payee
- id: integer (PK, auto-generated)
- name: string (required, max 255)
- type: enum [CLAIMANT, VENDOR, MEDICAL_PROVIDER, ATTORNEY, OTHER] (required)
- tax_id: string (encrypted, max 20)
- tax_id_masked: string (computed, shows last 4 digits only)
- address: string (required, max 255)
- city: string (required, max 100)
- state: string (required, exactly 2 chars)
- zip_code: string (required, max 10)
- kyc_verified: boolean (default: false)
- kyc_verified_at: datetime (nullable)
- active: boolean (default: true)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

**Relationships:**
- Payee 1:N PaymentMethod (one payee has multiple payment methods)
- Payee 1:N PaymentPayee (payee receives multiple payments)

### PaymentMethod
- id: integer (PK, auto-generated)
- payee_id: integer (FK to Payee, required)
- method_type: enum [ACH, WIRE, CREDIT_CARD, DEBIT_CARD, STRIPE_CONNECT] (required)
- account_details: text (encrypted, required)
- routing_details: text (encrypted, nullable)
- verification_status: enum [UNVERIFIED, PENDING, VERIFIED, FAILED] (default: UNVERIFIED)
- is_default: boolean (default: false)
- active: boolean (default: true)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

### PaymentPayee
- id: integer (PK, auto-generated)
- payment_id: integer (FK to Payment, required)
- payee_id: integer (FK to Payee, required)
- payment_method_id: integer (FK to PaymentMethod, required)
- amount: decimal(15,2) (required)
- portion_percentage: decimal(5,2) (required, min 0, max 100)
- is_joint_payee: boolean (default: false)
- created_at: datetime (auto-set, required)

### PaymentReserveAllocation
- id: integer (PK, auto-generated)
- payment_id: integer (FK to Payment, required)
- reserve_id: integer (FK to Reserve, required)
- allocated_amount: decimal(15,2) (required)
- created_at: datetime (auto-set, required)

### Settlement
- id: integer (PK, auto-generated)
- claim_id: integer (FK to Claim, required)
- settlement_amount: decimal(15,2) (required)
- settlement_date: date (required)
- status: enum [PROPOSED, NEGOTIATING, APPROVED, REJECTED, COMPLETED] (required, default: PROPOSED)
- approval_level_required: enum [ADJUSTER, SUPERVISOR, MANAGER, EXECUTIVE] (required)
- approved_by: integer (FK to User, nullable)
- approved_at: datetime (nullable)
- notes: text (nullable)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

### AuditLog
- id: integer (PK, auto-generated)
- entity_type: string (required, max 100)
- entity_id: integer (required)
- operation: enum [CREATE, UPDATE, DELETE] (required)
- field_name: string (nullable, max 100)
- old_value: text (nullable)
- new_value: text (nullable)
- user_id: integer (FK to User, required)
- correlation_id: string (required, max 100, for request tracing)
- ip_address: string (required, max 45)
- user_agent: string (nullable, max 500)
- created_at: datetime (auto-set, required)

### ExternalIntegration
- id: integer (PK, auto-generated)
- integration_name: string (required, max 100)
- endpoint_url: string (required, max 500)
- authentication_type: enum [API_KEY, OAUTH2, BASIC_AUTH] (required)
- credentials: text (encrypted, required)
- timeout_seconds: integer (default: 30)
- retry_attempts: integer (default: 3)
- circuit_breaker_threshold: integer (default: 5)
- active: boolean (default: true)
- created_at: datetime (auto-set, required)
- updated_at: datetime (auto-set, required)

## Integration Requirements

### External Systems Integration

**Stripe Connect Integration:**
- Trigger: Payment processing for credit/debit cards
- Data Sent: Payment amount, recipient details, payment metadata
- Data Received: Transaction ID, status, processing fees
- Error Handling: Retry failed transactions, handle insufficient funds, expired cards

**Global Payouts Integration:**
- Trigger: International payment processing
- Data Sent: Recipient country, currency, amount, KYC information
- Data Received: Payout status, exchange rates, compliance checks
- Error Handling: Handle currency restrictions, compliance failures, recipient verification issues

**Bank ACH/Wire Integration:**
- Trigger: Domestic bank transfers
- Data Sent: Account numbers, routing numbers, amounts, transaction codes
- Data Received: Transaction confirmations, settlement status
- Error Handling: Invalid account information, insufficient funds, bank holidays

**Xactimate/XactAnalysis Integration:**
- Trigger: Estimate import for claim processing
- Data Sent: Claim number, property details, loss information
- Data Received: Line item estimates, total amounts, scope of work
- Error Handling: Invalid claim data, service unavailable, estimate format errors

**Document Management Integration:**
- Trigger: Document upload/retrieval for policies, claims, payments
- Data Sent: Document metadata, file content, entity relationships
- Data Received: Document IDs, storage confirmation, retrieval URLs
- Error Handling: File size limits, unsupported formats, storage failures

**EDI 835/837 Integration:**
- Trigger: Medical payment processing
- Data Sent: Claim details, procedure codes, payment amounts
- Data Received: Acknowledgments, status updates, rejection reasons
- Error Handling: Invalid formats, missing required fields, provider issues

**General Ledger Integration:**
- Trigger: Financial transaction posting
- Data Sent: Account codes, transaction amounts, descriptions
- Data Received: Posting confirmations, account balances
- Error Handling: Invalid account codes, posting period closed, balance discrepancies

**Tax ID Verification Integration:**
- Trigger: Payee setup and tax reporting
- Data Sent: Tax ID numbers, payee information
- Data Received: Verification status, entity details
- Error Handling: Invalid tax IDs, verification service downtime

### Integration Patterns

**Circuit Breaker Pattern:**
- Monitor failure rates for each integration
- Open circuit after 5 consecutive failures
- Half-open state for testing recovery
- Full recovery after successful operations

**Retry Logic:**
- Exponential backoff: 1s, 2s, 4s, 8s
- Maximum 3 retry attempts per request
- Different retry strategies per integration type
- Dead letter queue for permanently failed requests

**Timeout Management:**
- Default 30-second timeout for API calls
- Configurable per integration type
- Connection timeout: 5 seconds
- Read timeout: Based on operation complexity

**Error Handling:**
- Standardized error response format
- Error categorization: Temporary, Permanent, Business Rule
- Automatic retry for temporary errors
- Manual intervention required for permanent errors

## Traceability Matrix

| Requirement ID | Feature | Priority | NFR Category |
|---------------|---------|----------|--------------|
| US-001 | auth-login | High | Security |
| US-002 | rbac-authorization | High | Security |
| US-003 | policy-search | High | Performance |
| US-004 | policy-details | High | Performance |
| US-005 | policy-create | Medium | Reliability |
| US-006 | policy-update | Medium | Reliability |
| US-007 | claim-create | High | Reliability |
| US-008 | claim-history | Medium | Performance |
| US-009 | claim-policy-override | Medium | Reliability |
| US-010 | claim-status-management | High | Reliability |
| US-011 | payment-method-setup | High | Security |
| US-012 | payment-create | High | Security |
| US-013 | payment-lifecycle | High | Reliability |
| US-014 | tax-reporting | Medium | Security |
| US-015 | edi-medical-payments | Medium | Reliability |
| US-016 | settlement-management | Medium | Reliability |
| US-017 | external-integrations | High | Scalability |
| BR-001-015 | data-validation | High | Reliability |
| NFR-Security | encryption-masking | High | Security |
| NFR-Performance | response-times | High | Performance |
| NFR-Observability | audit-logging | High | Observability |
| NFR-Reliability | error-handling | High | Reliability |
| NFR-Scalability | stateless-design | Medium | Scalability |

## Open Questions

1. **Payment Authorization Limits:** What are the specific dollar amount thresholds that require different approval levels (adjuster, supervisor, manager, executive)?

2. **Data Retention Policies:** How long should audit logs, completed claims, and payment records be retained? Are there regulatory requirements for specific retention periods?

3. **Multi-Currency Support:** Does the system need to support multiple currencies for global payouts, and what are the specific currencies required?

4. **Integration Priorities:** Which external integrations are required for MVP vs. future phases? Should Xactimate integration be prioritized over EDI 835/837?

5. **Performance SLA Details:** Are the specified response times (3s for search, 5s for details/payments) based on specific user volumes or concurrent session counts?

6. **Disaster Recovery:** What are the RTO (Recovery Time Objective) and RPO (Recovery Point Objective) requirements for system availability?

7. **Compliance Certifications:** Besides PCI-DSS, are there other compliance requirements (SOX, HIPAA for medical payments, state insurance regulations)?

8. **User Session Management:** What should be the default JWT token expiration time, and should there be refresh token functionality?

9. **File Upload Limits:** What are the maximum file sizes and supported formats for document attachments to policies, claims, and payments?

10. **Notification Requirements:** Should the system send email/SMS notifications for claim status changes, payment completions, or settlement approvals?