# Database Design: auh-sys (Integrated Policy, Claims, and Payments Platform)

## Overview

This document provides the complete database design for the auh-sys insurance platform, including entity-relationship diagram, table definitions, indexes, and design rationale.

**Technology Stack:**
- ORM: SQLAlchemy 2.0
- Migration Tool: Alembic
- Database: PostgreSQL 16 (production), SQLite 3 (development)
- Language: Python 3.12
- Framework: FastAPI

---

## Entity-Relationship Diagram (Text Format)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUTHENTICATION & AUDIT                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐      1:N      ┌──────────────┐                           │
│  │ users        │──────────────>│ audit_logs   │                           │
│  └──────────────┘               └──────────────┘                           │
│       │ 1:N                                                                  │
│       │                                                                      │
│       └──────────────────────────────────────────────────────────────┐      │
│                                                                      │      │
└──────────────────────────────────────────────────────────────────────┼──────┘
                                                                       │
                                                              (Audit Trail)
                                                                       │
┌──────────────────────────────────────────────────────────────────────┼──────┐
│                         POLICY MANAGEMENT                            │      │
├──────────────────────────────────────────────────────────────────────┼──────┤
│                                                                      │      │
│  ┌──────────────┐     1:N     ┌──────────────┐                      │      │
│  │ insureds     │────────────>│ policies     │◄─────────────────────┘      │
│  └──────────────┘             └──────────────┘                             │
│                                     │ 1:N                                   │
│                        ┌────────────┼────────────┐                          │
│                        │            │            │                          │
│                        ▼            ▼            ▼                          │
│                  ┌──────────┐  ┌──────────┐  ┌────────────┐                │
│                  │coverages │  │vehicles  │  │endorsements│                │
│                  └──────────┘  └──────────┘  └────────────┘                │
│                                     │                                       │
│                                     ▼                                       │
│                               ┌──────────┐                                  │
│                               │locations │                                  │
│                               └──────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLAIMS MANAGEMENT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐         ┌────────────────────┐         ┌─────────────┐   │
│  │ policies     │◄────┐   │ claims             │    ┌───>│ reserve_    │   │
│  └──────────────┘     │   │                    │    │    │ lines       │   │
│                       N:1 │                    │    │1:N └─────────────┘   │
│  ┌──────────────┐        └────────────────────┘    │                       │
│  │              │            │         │           │                       │
│  │ (via policy) │            │1:N      │1:N        │                       │
│  └──────────────┘            │         │           │                       │
│                              │         │           │                       │
│                              ▼         ▼           │                       │
│                        ┌────────────────────┐     │                       │
│                        │ claim_adjustments  │     │                       │
│                        └────────────────────┘     │                       │
│                                                   │                       │
│  ┌──────────────────────────────────────────┐   │                       │
│  │ claim_level_policies (unverified data)   │◄──┘                       │
│  └──────────────────────────────────────────┘ 1:1                       │
│                                                                          │
│  ┌──────────────────────────────────────────┐                          │
│  │ other_carrier_info (party data)          │◄─ 1:1                    │
│  └──────────────────────────────────────────┘                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    PAYMENTS & DISBURSEMENTS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │ policies     │    │ claims       │    │ reserve_     │                  │
│  │ (N:1)        │───>│ (N:1)        │───>│ lines (0:1)  │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                              │                      │                       │
│                              │ N:1                  │                       │
│                              │                      │                       │
│                              ▼                      ▼                       │
│                        ┌────────────────────────────────┐                   │
│                        │ payments                       │                   │
│                        │ (supports multiple methods)    │                   │
│                        └────────────────────────────────┘                   │
│                              │ N:1                                           │
│                              ▼                                               │
│                        ┌────────────────────┐                               │
│                        │ payees             │                               │
│                        └────────────────────┘                               │
│                              │ 1:N                                           │
│                    ┌─────────┼─────────┐                                    │
│                    │         │         │                                    │
│                    ▼         ▼         ▼                                    │
│            ┌────────────┐  ┌──────────────┐  ┌────────────────┐            │
│            │payment_    │  │payment_      │  │payment_        │            │
│            │details     │  │deductions    │  │documents       │            │
│            └────────────┘  └──────────────┘  └────────────────┘            │
│                                                                              │
│  ┌─────────────────────────┐                                               │
│  │ payment_methods         │ (ACH, Wire, Card, Stripe, GlobalPayouts)      │
│  │ (1:N per payee)         │                                               │
│  └─────────────────────────┘                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION & SUPPORT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────┐     ┌──────────────────────────┐             │
│  │ scheduled_payments       │     │ external_estimates       │             │
│  │ (Subrogation tracking)   │     │ (Xactimate/XactAnalysis)│             │
│  └──────────────────────────┘     └──────────────────────────┘             │
│         Linked to: claims               Linked to: claims                  │
│                                                                              │
│  ┌──────────────────────────┐     ┌──────────────────────────┐             │
│  │ payment_routing_rules    │     │ tax_reportable_payments  │             │
│  │ (Business rule routing)  │     │ (Tax reporting)          │             │
│  └──────────────────────────┘     └──────────────────────────┘             │
│                                          Linked to: payees                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Table Definitions

### Authentication & Authorization

#### users
User accounts with role-based access control.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Y | — |
| password_hash | VARCHAR(255) | NOT NULL | N | — |
| first_name | VARCHAR(100) | NOT NULL | N | — |
| last_name | VARCHAR(100) | NOT NULL | N | — |
| role | ENUM(UserRole) | NOT NULL | N | AGENT |
| active | BOOLEAN | NOT NULL | Y | TRUE |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Roles:** AGENT, UNDERWRITER, CLAIMS_ADJUSTER, FINANCE_MANAGER, RECOVERY_MANAGER, ADMIN, AUDITOR

**Indexes:**
- `idx_users_email` - Fast email lookup for login
- `idx_users_active` - Filter by active status

---

#### roles
Role definitions for RBAC.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Y | — |
| description | VARCHAR(500) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_roles_name` - Fast role lookup

---

#### permissions
Fine-grained permissions linked to roles.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| role_id | INTEGER | FK(roles.id), NOT NULL | Y | — |
| code | VARCHAR(100) | NOT NULL | Y | — |
| description | VARCHAR(255) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_permissions_role_id` - FK lookup
- `idx_permissions_code` - Permission code lookup

---

#### audit_logs
Comprehensive audit trail for all system changes.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| user_id | INTEGER | FK(users.id), NOT NULL | Y | — |
| entity_type | VARCHAR(100) | NOT NULL | Y | — |
| entity_id | INTEGER | NOT NULL | Y | — |
| action | VARCHAR(50) | NOT NULL | N | — |
| changes | TEXT | NULLABLE | N | — |
| ip_address | VARCHAR(50) | NULLABLE | N | — |
| user_agent | VARCHAR(500) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | Y | func.now() |

**Indexes:**
- `idx_audit_logs_user_id` - Filter by user
- `idx_audit_logs_created_at` - Time-range queries
- `idx_audit_logs_entity_type` - Filter by entity type
- `idx_audit_logs_entity_id` - Find all changes to entity

**Note:** `created_at` is the only timestamp (no updates to audit logs)

---

### Policy Management

#### insureds
Party information (insured, claimant, payee, etc.).

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| first_name | VARCHAR(100) | NOT NULL | N | — |
| last_name | VARCHAR(100) | NOT NULL | Y | — |
| email | VARCHAR(255) | NULLABLE | Y | — |
| phone | VARCHAR(20) | NULLABLE | N | — |
| tax_id | VARCHAR(50) | NULLABLE | Y | — |
| address | VARCHAR(255) | NULLABLE | N | — |
| city | VARCHAR(100) | NULLABLE | N | — |
| state | VARCHAR(2) | NULLABLE | N | — |
| zip_code | VARCHAR(10) | NULLABLE | N | — |
| organization_name | VARCHAR(255) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_insureds_email` - Email lookup
- `idx_insureds_tax_id` - SSN/TIN lookup (encrypted)
- `idx_insureds_name` - Name-based search

---

#### policies
Insurance policies with complete lifecycle management.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| policy_number | VARCHAR(100) | UNIQUE, NOT NULL | Y | — |
| insured_id | INTEGER | FK(insureds.id), NOT NULL | Y | — |
| policy_type | ENUM(PolicyType) | NOT NULL | N | — |
| status | ENUM(PolicyStatus) | NOT NULL | Y | ACTIVE |
| effective_date | DATE | NOT NULL | Y | — |
| expiration_date | DATE | NOT NULL | N | — |
| premium_amount | NUMERIC(15,2) | NOT NULL | N | — |
| deductible_amount | NUMERIC(15,2) | NOT NULL | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Policy Types:** AUTO, PROPERTY, LIABILITY, WORKERS_COMP, HEALTH, OTHER

**Policy Statuses:** ACTIVE, INACTIVE, EXPIRED, CANCELLED

**Indexes:**
- `idx_policies_policy_number` - Policy search
- `idx_policies_status` - Filter by status
- `idx_policies_insured_id` - FK lookup
- `idx_policies_effective_date` - Date range queries

---

#### coverages
Coverage types, limits, and deductibles.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| policy_id | INTEGER | FK(policies.id), NOT NULL | Y | — |
| coverage_type | ENUM(CoverageType) | NOT NULL | N | — |
| limit_amount | NUMERIC(15,2) | NOT NULL | N | — |
| deductible_amount | NUMERIC(15,2) | NOT NULL | N | — |
| premium_amount | NUMERIC(15,2) | NOT NULL | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Coverage Types:** LIABILITY, COLLISION, COMPREHENSIVE, UNINSURED_MOTORIST, MEDICAL_PAYMENTS, OTHER

**Indexes:**
- `idx_coverages_policy_id` - FK lookup

---

#### vehicles
Vehicle details for auto policies.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| policy_id | INTEGER | FK(policies.id), NOT NULL | Y | — |
| year | INTEGER | NOT NULL | N | — |
| make | VARCHAR(100) | NOT NULL | N | — |
| model | VARCHAR(100) | NOT NULL | N | — |
| vin | VARCHAR(17) | UNIQUE, NOT NULL | Y | — |
| license_plate | VARCHAR(20) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_vehicles_policy_id` - FK lookup
- `idx_vehicles_vin` - VIN search

---

#### locations
Location/address details for policies.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| policy_id | INTEGER | FK(policies.id), NOT NULL | Y | — |
| address | VARCHAR(255) | NOT NULL | N | — |
| city | VARCHAR(100) | NOT NULL | N | — |
| state | VARCHAR(2) | NOT NULL | N | — |
| zip_code | VARCHAR(10) | NOT NULL | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_locations_policy_id` - FK lookup

---

#### endorsements
Policy modifications and endorsements.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| policy_id | INTEGER | FK(policies.id), NOT NULL | Y | — |
| endorsement_number | VARCHAR(50) | NOT NULL | N | — |
| description | VARCHAR(500) | NULLABLE | N | — |
| effective_date | DATE | NOT NULL | N | — |
| expiration_date | DATE | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_endorsements_policy_id` - FK lookup

---

### Claims Management

#### claims
Claims linked to policies with full lifecycle support.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| claim_number | VARCHAR(100) | UNIQUE, NOT NULL | Y | — |
| policy_id | INTEGER | FK(policies.id), NOT NULL | Y | — |
| date_of_loss | DATE | NOT NULL | Y | — |
| date_reported | DATE | NOT NULL | N | — |
| status | ENUM(ClaimStatus) | NOT NULL | Y | OPEN |
| description | TEXT | NULLABLE | N | — |
| injury_details | TEXT | NULLABLE | N | — |
| carrier_involvement | VARCHAR(255) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Claim Statuses:** OPEN, UNDER_INVESTIGATION, CLOSED, PAID, DENIED

**Indexes:**
- `idx_claims_claim_number` - Claim search
- `idx_claims_policy_id` - FK lookup
- `idx_claims_status` - Filter by status
- `idx_claims_date_of_loss` - Sort by loss date

---

#### claim_adjustments
Adjustments and updates to claim values.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| claim_id | INTEGER | FK(claims.id), NOT NULL | Y | — |
| adjustment_type | VARCHAR(100) | NOT NULL | N | — |
| adjustment_amount | NUMERIC(15,2) | NOT NULL | N | — |
| reason | TEXT | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_claim_adjustments_claim_id` - FK lookup

---

#### reserve_lines
Reserve allocations for claims.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| claim_id | INTEGER | FK(claims.id), NOT NULL | Y | — |
| reserve_type | VARCHAR(100) | NOT NULL | N | — |
| total_reserve | NUMERIC(15,2) | NOT NULL | N | — |
| used_amount | NUMERIC(15,2) | NOT NULL | N | 0 |
| remaining_balance | NUMERIC(15,2) | NOT NULL | N | — |
| is_eroding | BOOLEAN | NOT NULL | N | TRUE |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_reserve_lines_claim_id` - FK lookup

---

#### claim_level_policies
Claim-specific policy data when policy is unverified.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| claim_id | INTEGER | FK(claims.id), NOT NULL | Y | — |
| policy_number | VARCHAR(100) | NULLABLE | N | — |
| insured_name | VARCHAR(200) | NULLABLE | N | — |
| policy_type | VARCHAR(100) | NULLABLE | N | — |
| coverage_details | TEXT | NULLABLE | N | — |
| is_verified | BOOLEAN | NOT NULL | N | FALSE |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_claim_level_policies_claim_id` - FK lookup

**Note:** Tracked separately; does not overwrite original policy data

---

#### other_carrier_info
Other carrier party and payment information for claims.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| claim_id | INTEGER | FK(claims.id), NOT NULL | Y | — |
| carrier_name | VARCHAR(255) | NULLABLE | N | — |
| claim_number | VARCHAR(100) | NULLABLE | N | — |
| contact_name | VARCHAR(200) | NULLABLE | N | — |
| contact_phone | VARCHAR(20) | NULLABLE | N | — |
| contact_email | VARCHAR(255) | NULLABLE | N | — |
| payment_info | TEXT | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_other_carrier_info_claim_id` - FK lookup

---

### Payments & Disbursements

#### payees
Vendor/claimant onboarding with KYC/identity verification.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| name | VARCHAR(255) | NOT NULL | Y | — |
| email | VARCHAR(255) | NULLABLE | Y | — |
| phone | VARCHAR(20) | NULLABLE | N | — |
| tax_id | VARCHAR(50) | NULLABLE | Y | — |
| address | VARCHAR(255) | NULLABLE | N | — |
| city | VARCHAR(100) | NULLABLE | N | — |
| state | VARCHAR(2) | NULLABLE | N | — |
| zip_code | VARCHAR(10) | NULLABLE | N | — |
| kyc_verified | BOOLEAN | NOT NULL | N | FALSE |
| kyc_document_url | VARCHAR(500) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_payees_tax_id` - Tax ID lookup (encrypted)
- `idx_payees_email` - Email lookup
- `idx_payees_name` - Payee search

---

#### payment_methods
Payment method details for payees (ACH, Wire, Card, Stripe, etc.).

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| payee_id | INTEGER | FK(payees.id), NOT NULL | Y | — |
| method_type | ENUM(PaymentMethodType) | NOT NULL | N | — |
| is_primary | BOOLEAN | NOT NULL | N | FALSE |
| account_number | VARCHAR(255) | NULLABLE | N | — |
| routing_number | VARCHAR(20) | NULLABLE | N | — |
| bank_name | VARCHAR(255) | NULLABLE | N | — |
| account_holder_name | VARCHAR(255) | NULLABLE | N | — |
| stripe_customer_id | VARCHAR(255) | NULLABLE | N | — |
| is_verified | BOOLEAN | NOT NULL | N | FALSE |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Payment Methods:** ACH, WIRE, CARD, STRIPE, GLOBAL_PAYOUTS

**Indexes:**
- `idx_payment_methods_payee_id` - FK lookup

**Note:** Account numbers encrypted at rest

---

#### payments
Payment transactions linked to claims/policies.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| payment_number | VARCHAR(100) | UNIQUE, NOT NULL | Y | — |
| claim_id | INTEGER | FK(claims.id), NULLABLE | Y | — |
| policy_id | INTEGER | FK(policies.id), NULLABLE | Y | — |
| payee_id | INTEGER | FK(payees.id), NOT NULL | Y | — |
| reserve_line_id | INTEGER | FK(reserve_lines.id), NULLABLE | Y | — |
| payment_method | ENUM(PaymentMethodType) | NOT NULL | N | — |
| status | ENUM(PaymentStatus) | NOT NULL | Y | PENDING |
| amount | NUMERIC(15,2) | NOT NULL | N | — |
| is_eroding | BOOLEAN | NOT NULL | N | TRUE |
| is_tax_reportable | BOOLEAN | NOT NULL | N | FALSE |
| notes | TEXT | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Payment Statuses:** PENDING, APPROVED, PROCESSING, COMPLETED, FAILED, VOIDED, REVERSED

**Indexes:**
- `idx_payments_payment_number` - Payment search
- `idx_payments_claim_id` - FK lookup
- `idx_payments_policy_id` - FK lookup
- `idx_payments_payee_id` - FK lookup
- `idx_payments_status` - Filter by status

**Features:**
- Supports positive, negative, and zero amounts
- Eroding vs non-eroding designation for reserve allocation
- Multiple payment methods (ACH, Wire, Card, Stripe, Global Payouts)
- Tax reportable marking for 1099/W2 reporting

---

#### payment_details
Line items/details for payment transactions.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| payment_id | INTEGER | FK(payments.id), NOT NULL | Y | — |
| detail_type | VARCHAR(100) | NOT NULL | N | — |
| description | VARCHAR(500) | NULLABLE | N | — |
| amount | NUMERIC(15,2) | NOT NULL | N | — |
| additional_info | TEXT | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_payment_details_payment_id` - FK lookup

---

#### payment_deductions
Tax withholding and other deductions from payments.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| payment_id | INTEGER | FK(payments.id), NOT NULL | Y | — |
| deduction_type | VARCHAR(100) | NOT NULL | N | — |
| deduction_amount | NUMERIC(15,2) | NOT NULL | N | — |
| reason | VARCHAR(255) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_payment_deductions_payment_id` - FK lookup

**Example Deduction Types:** INCOME_TAX, MEDICARE, SOCIAL_SECURITY, etc.

---

#### payment_documents
Document attachments to payment transactions.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| payment_id | INTEGER | FK(payments.id), NOT NULL | Y | — |
| document_name | VARCHAR(255) | NOT NULL | N | — |
| document_url | VARCHAR(500) | NOT NULL | N | — |
| document_type | VARCHAR(100) | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_payment_documents_payment_id` - FK lookup

---

### Integration & Support

#### scheduled_payments
Subrogation scheduled payment tracking.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| claim_id | INTEGER | FK(claims.id), NOT NULL | Y | — |
| payee_name | VARCHAR(255) | NOT NULL | N | — |
| scheduled_date | DATE | NOT NULL | N | — |
| payment_type | VARCHAR(100) | NOT NULL | N | — |
| total_amount | NUMERIC(15,2) | NOT NULL | N | — |
| paid_amount | NUMERIC(15,2) | NOT NULL | N | 0 |
| remaining_balance | NUMERIC(15,2) | NOT NULL | N | — |
| status | ENUM(ScheduledPaymentStatus) | NOT NULL | Y | PENDING |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Statuses:** PENDING, DUE, PAID, OVERDUE

**Indexes:**
- `idx_scheduled_payments_claim_id` - FK lookup
- `idx_scheduled_payments_status` - Filter by status

---

#### external_estimates
Payable line items from external estimates (Xactimate/XactAnalysis).

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| claim_id | INTEGER | FK(claims.id), NOT NULL | Y | — |
| estimate_number | VARCHAR(100) | NOT NULL | N | — |
| source_system | VARCHAR(100) | NOT NULL | N | — |
| line_item_description | TEXT | NULLABLE | N | — |
| item_amount | NUMERIC(15,2) | NOT NULL | N | — |
| is_payable | BOOLEAN | NOT NULL | N | FALSE |
| additional_metadata | TEXT | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_external_estimates_claim_id` - FK lookup

**Source Systems:** XACTIMATE, XACTANALYSIS, etc.

---

#### payment_routing_rules
Business rules for payment routing based on payee, type, and conditions.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| rule_name | VARCHAR(255) | UNIQUE, NOT NULL | N | — |
| rule_type | VARCHAR(100) | NOT NULL | N | — |
| payee_filter | TEXT | NULLABLE | N | — |
| payment_type_filter | VARCHAR(100) | NULLABLE | N | — |
| routing_target | VARCHAR(255) | NOT NULL | N | — |
| is_active | BOOLEAN | NOT NULL | N | TRUE |
| description | TEXT | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Note:** `payee_filter` stored as JSON for flexible filtering

---

#### tax_reportable_payments
Tax reporting details for payments.

| Column | Type | Constraints | Index | Default |
|--------|------|-------------|-------|---------|
| id | INTEGER | PK, AUTOINCREMENT | Y | — |
| payee_id | INTEGER | FK(payees.id), NOT NULL | Y | — |
| tax_year | INTEGER | NOT NULL | N | — |
| total_amount | NUMERIC(15,2) | NOT NULL | N | — |
| tax_form_type | VARCHAR(50) | NULLABLE | N | — |
| tax_id | VARCHAR(50) | NULLABLE | N | — |
| tax_id_type | VARCHAR(20) | NULLABLE | N | — |
| additional_info | TEXT | NULLABLE | N | — |
| created_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |
| updated_at | TIMESTAMP(TZ) | NOT NULL | N | func.now() |

**Indexes:**
- `idx_tax_reportable_payments_payee_id` - FK lookup

**Tax ID Types:** SSN, EIN, ITIN

---

## Indexing Strategy

### Primary Keys
- **All tables:** `id` (INTEGER, AUTOINCREMENT, PRIMARY KEY)
- Indexed for fast lookups and join operations

### Foreign Key Indexes
Every foreign key column is indexed for:
- Fast JOIN operations
- Relationship traversal
- Delete cascade operations

**Foreign Key Columns (All Indexed):**
- `users → roles` (via roles table)
- `policies → insureds`
- `claims → policies`
- `payments → claims, policies, payees, reserve_lines`
- `payees → payment_methods`
- `reserve_lines → claims`
- And others (see individual table definitions)

### Search & Filter Indexes
- **Email fields:** Indexed for login and contact lookup
- **Policy Number:** Indexed for policy search (3-second SLA)
- **Claim Number:** Indexed for claim search
- **Tax ID:** Indexed for payee identification (encrypted)
- **Status fields:** Indexed for filtering claims and payments
- **Date fields:** Indexed for range queries (loss date, effective date)
- **Name fields:** Indexed for text-based search

### Covering Indexes (Future Optimization)
- `payments(payee_id, status, created_at)` for recent payee payments
- `claims(policy_id, status, date_of_loss)` for claim history

---

## Audit Trail Design

### AuditLog Table
- **Non-destructive:** All audit logs are immutable (created_at only)
- **Correlation:** Every log entry links to `users.id` and tracks `entity_type`, `entity_id`, `action`
- **Changes:** JSON diff stored in `changes` column for audit purposes
- **Metadata:** `ip_address` and `user_agent` for security tracking

### Audit Fields on All Models
- **created_at:** Server-side default (`func.now()`) - when entity was created
- **updated_at:** Server-side default and onupdate (`func.now()`) - last modification time
- Both columns are timezone-aware (`DateTime(timezone=True)`)

---

## Performance Considerations

### Response Time SLAs
- Policy search: **< 3 seconds** (via `idx_policies_policy_number`, `idx_policies_status`)
- Policy details: **< 5 seconds** (single JOIN via FK index)
- Claim history: **< 5 seconds** (multi-row fetch via `idx_claims_policy_id`, sorting by `idx_claims_date_of_loss`)
- Payment processing: **< 5 seconds** (insert + relationship updates)

### Scaling Strategies
1. **Partitioning:** Partition `audit_logs` by `created_at` (quarterly)
2. **Archive:** Move old audit logs (>2 years) to archive table or separate DB
3. **Read Replicas:** Use PostgreSQL streaming replication for read-heavy operations
4. **Caching:** Cache frequently-accessed policies, payees, and routing rules in Redis

---

## Security Considerations

### Encryption at Rest
- **SSN/TIN:** Stored encrypted in `insureds.tax_id`, `payees.tax_id`, `tax_reportable_payments.tax_id`
- **Account Numbers:** Encrypted in `payment_methods.account_number`
- **Implementation:** AES-256 encryption at application layer before storing

### Encryption in Transit
- **HTTPS/TLS 1.2+:** All API communication
- **Database Connections:** SSL/TLS for PostgreSQL connections

### Audit Trail
- **Immutable Logs:** AuditLog entries never updated or deleted
- **User Tracking:** Every change linked to `users.id`
- **Action Tracking:** `action` field (CREATE, UPDATE, DELETE)
- **Change Diff:** JSON diff in `changes` column

### PII Masking
- **Display Layer:** Mask SSN as XXX-XX-1234, account numbers as ****7890
- **Logging:** Never log full SSN, account numbers, or payment tokens
- **Database:** Never log plaintext PII in audit_logs.changes

---

## Design Decisions

### 1. **Audit Mixin (Mandatory)**
All models inherit from `AuditMixin` with `id`, `created_at`, `updated_at`.
- **Rationale:** Enables audit trail and optimistic locking across all entities
- **Exception:** `AuditLog` table has only `created_at` (immutable)

### 2. **Hard Deletes (No Soft Deletes)**
Entities are hard-deleted; audit trail enables recovery if needed.
- **Rationale:** Simpler schema, easier compliance with deletion requests, audit logs provide recovery path

### 3. **Relationships with Cascade**
Most relationships use `cascade="all, delete-orphan"` for parent-child.
- **Rationale:** Ensures data integrity; orphaned records auto-cleanup
- **Examples:** Policy → Coverage, Claim → ReserveLine, Payment → PaymentDetail

### 4. **Numeric Decimals (Not Floats)**
All monetary amounts use `NUMERIC(15, 2)`.
- **Rationale:** Prevents floating-point precision loss (critical for financial data)

### 5. **String-Based Enums in DB**
Enum columns stored as VARCHAR with CHECK constraint (SQLAlchemy Enum).
- **Rationale:** Human-readable, easier migrations, database portability

### 6. **Timezone-Aware Timestamps**
All timestamps use `DateTime(timezone=True)`.
- **Rationale:** Correct handling of DST, multi-region queries, audit trail accuracy

### 7. **Separate Claims Policy Data**
`ClaimLevelPolicy` table (not embedded in Claim).
- **Rationale:** Allows tracking unverified policy data separately without overwriting original
- **Feature:** Visual indicator can flag when claim-level data differs from actual policy

### 8. **Payment Routing Rules**
Configurable business rules separate from code logic.
- **Rationale:** Enables runtime configuration without code deployment
- **Storage:** JSON filters for flexible, dynamic routing conditions

### 9. **Multi-Method Payment Support**
Single `Payment` record with flexible `PaymentMethod` selection.
- **Rationale:** Simplifies payment creation, supports method switching, audit-friendly

### 10. **Tax Reportable Payments**
Separate table for tax reporting aggregation.
- **Rationale:** Decouples tax reporting from payment transactions, enables bulk tax filing

---

## Migration Strategy

### Initial Migration
- **File:** `alembic/versions/001_create_initial_schema.py` (auto-generated)
- **Command:** `alembic upgrade head`
- **Effect:** Creates all tables, indexes, constraints, and relationships

### Future Migrations
All schema changes via Alembic versioned migrations:
```bash
# Create new migration
alembic revision --autogenerate -m "add_new_field_to_payments"

# Review generated migration file
# (edit if needed)

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Additive Migrations Preferred:**
1. Add column (`ALTER TABLE ... ADD COLUMN`)
2. Backfill data (if needed)
3. Add NOT NULL constraint (if needed)

**Never:** Drop columns/tables without explicit requirement and backup

---

## Conclusion

This database design provides:
- ✓ Complete audit trail for compliance
- ✓ Flexible payment processing (multiple methods, reserves, deductions)
- ✓ Policy lifecycle management
- ✓ Claims with separate unverified policy data
- ✓ PII encryption and masking support
- ✓ Performance indexing for 3-5 second SLAs
- ✓ Scalability (partitioning, archiving, read replicas)
- ✓ Security (encryption, audit, RBAC, immutable logs)

All models follow SQLAlchemy 2.0 best practices with type-safe `Mapped` annotations and explicit relationship configuration.
