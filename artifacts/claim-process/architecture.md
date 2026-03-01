# Architecture: Integrated Policy, Claims, and Payments Platform

## System Overview
A unified platform for managing insurance policies, claims, and payments with secure workflows and regulatory compliance.

## Technology Decisions

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLAlchemy 2.0 (async), SQLite (dev), PostgreSQL (prod)
- **Authentication**: JWT with Bearer tokens
- **Validation**: Pydantic v2
- **API Style**: RESTful

### Security
- **Password Hashing**: bcrypt via passlib
- **Token Management**: python-jose with HS256
- **Data Masking**: SSN/TIN masked to last 4 digits
- **Encryption**: All sensitive data encrypted at rest
- **Compliance**: PCI-DSS for payment data, WCAG for accessibility

## Data Model

### Core Entities

#### User
- id (PK)
- email (unique)
- password_hash
- name
- role (admin, adjuster, agent)
- created_at, updated_at

#### Policy
- id (PK)
- policy_number (unique, indexed)
- insured_first_name
- insured_last_name
- organization_name
- ssn_tin (encrypted)
- policy_type
- effective_date
- expiration_date
- status (active, expired, cancelled)
- vehicle_year, vehicle_make, vehicle_model, vehicle_vin
- address, city, state, zip
- coverage_types (JSON)
- coverage_limits (JSON)
- coverage_deductibles (JSON)
- created_by, updated_by
- created_at, updated_at

#### Claim
- id (PK)
- claim_number (unique, indexed)
- policy_id (FK → Policy)
- loss_date
- claim_status (open, closed, paid, denied)
- description
- claim_level_policy_data (JSON, nullable) - for unverified policy data
- injury_incident_details (JSON)
- coding_information (JSON)
- carrier_involvement (JSON)
- referred_to_subrogation (boolean)
- scheduled_payment_applicable (boolean)
- scheduled_payment_type
- scheduled_payment_total
- scheduled_payment_balance
- scheduled_payment_current_due
- scheduled_payment_recipient
- created_by, updated_by
- created_at, updated_at

#### Payment
- id (PK)
- payment_number (unique, indexed)
- claim_id (FK → Claim)
- policy_id (FK → Policy)
- payment_method (ach, wire, card, stripe, global_payout)
- payment_type
- total_amount (can be positive, negative, or zero)
- status (pending, approved, issued, void, reversed)
- is_eroding (boolean) - whether payment erodes reserve
- is_tax_reportable (boolean)
- tax_id_number (encrypted, nullable)
- payment_date
- void_date, void_reason
- reversal_date, reversal_reason
- reissue_date
- reserve_lines (JSON) - allocation across multiple reserve lines
- created_by, updated_by
- created_at, updated_at

#### PaymentDetail
- id (PK)
- payment_id (FK → Payment)
- payee_type (vendor, claimant, provider)
- payee_id (FK → Vendor or User)
- payee_name
- payment_portion (decimal)
- deduction_amount (decimal, nullable)
- deduction_reason
- banking_info (JSON, encrypted) - for EFT/wire
- created_at

#### Vendor
- id (PK)
- vendor_name
- vendor_type (contractor, medical_provider, attorney)
- payment_method_verified (boolean)
- kyc_status (pending, verified, failed)
- tax_id (encrypted)
- banking_info (JSON, encrypted)
- stripe_account_id (nullable)
- created_at, updated_at

#### AuditLog
- id (PK)
- entity_type (policy, claim, payment)
- entity_id
- action (create, update, delete, view)
- user_id (FK → User)
- changes (JSON) - before/after values
- ip_address
- created_at

#### Document
- id (PK)
- entity_type (policy, claim, payment)
- entity_id
- document_type (estimate, invoice, photo, medical_bill)
- file_path
- file_name
- file_size
- uploaded_by (FK → User)
- created_at

## API Design

### Authentication
- POST /auth/register - Register new user
- POST /auth/login - Login and get JWT token
- GET /auth/me - Get current user info

### Policy Management
- GET /policies/search - Search policies (by policy_number, name, ssn_tin, type, dates, location)
- GET /policies/{id} - Get policy details
- POST /policies - Create policy
- PUT /policies/{id} - Update policy
- GET /policies/{id}/claims - Get claim history for policy

### Claims Management
- GET /claims/search - Search claims
- GET /claims/{id} - Get claim details
- POST /claims - Create claim
- PUT /claims/{id} - Update claim
- PUT /claims/{id}/policy-data - Update claim-level policy data
- POST /claims/{id}/refer-subrogation - Refer claim to subrogation

### Payments Management
- GET /payments/search - Search payments
- GET /payments/{id} - Get payment details
- POST /payments - Create payment
- PUT /payments/{id} - Update payment
- POST /payments/{id}/void - Void payment
- POST /payments/{id}/reverse - Reverse payment
- POST /payments/{id}/reissue - Reissue payment
- POST /payments/{id}/details - Add payment detail (payee)
- DELETE /payments/{id}/details/{detail_id} - Remove payment detail

### Vendor Management
- GET /vendors - List vendors
- GET /vendors/{id} - Get vendor details
- POST /vendors - Create/onboard vendor
- PUT /vendors/{id} - Update vendor
- POST /vendors/{id}/verify-payment-method - Verify payment method

### Audit & Reports
- GET /audit-logs - Query audit logs
- GET /reports/payment-summary - Payment summary report

## Component Design

### Service Layer
All business logic resides in service modules:
- **auth_service.py**: User registration, login, token management
- **policy_service.py**: Policy CRUD, search, validation, SSN masking
- **claim_service.py**: Claim CRUD, claim-level policy data management, subrogation
- **payment_service.py**: Payment lifecycle, void/reverse/reissue, reserve allocation
- **vendor_service.py**: Vendor onboarding, KYC verification
- **audit_service.py**: Audit log creation and retrieval

### Security Layer
- **JWT Authentication**: All endpoints (except auth) require valid JWT
- **Authorization**: Role-based access control (RBAC)
- **Data Masking**: SSN/TIN masked in responses
- **Encryption**: Sensitive fields encrypted at rest

### Middleware
- **CorrelationIdMiddleware**: Request tracing
- **RequestLoggingMiddleware**: Log all requests with duration
- **CORSMiddleware**: Configure allowed origins

### Exception Handling
- **NotFoundException**: 404 for missing resources
- **ConflictException**: 409 for duplicate resources
- **AuthException**: 401 for authentication failures
- **ForbiddenException**: 403 for authorization failures
- **ValidationException**: 400 for invalid input

## Integration Points

### External Systems (Future)
- Stripe Connect: Payment processing
- Xactimate/XactAnalysis: Estimate import
- EDI 835/837: Medical bill exchange
- Document Management: Document storage
- General Ledger: Accounting integration
- Bill Review: Medical bill review

*Note: External integrations are designed but not implemented in MVP. Placeholder endpoints and data structures are provided.*

## Performance Requirements
- Policy search: < 3 seconds
- Policy/claim details: < 5 seconds
- Payment processing: < 5 seconds
- Support 100+ concurrent users

## Security & Compliance
- All actions logged in audit_log
- SSN/TIN masked (show last 4 digits only)
- Payment data PCI-DSS compliant
- WCAG accessibility guidelines
- Role-based access control

## Deployment Architecture
- Application: FastAPI with Uvicorn
- Database: PostgreSQL (prod), SQLite (dev)
- Reverse Proxy: Nginx or cloud load balancer
- SSL/TLS: Required for all production endpoints
- Environment-based configuration via .env
