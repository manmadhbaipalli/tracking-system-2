# Database Design - Integrated Policy, Claims, and Payments Platform

## Entity Relationship Diagram (Text-Based)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CORE ENTITIES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────────┐│
│  │    User     │◄────┤  AuditLog   │────►│   Policy    │────►│   Claim      ││
│  │             │     │             │     │             │     │              ││
│  │ PK: id      │     │ PK: id      │     │ PK: id      │     │ PK: id       ││
│  │    email    │     │    entity_  │     │    number   │     │    number    ││
│  │    password │     │    type     │     │    type     │     │    status    ││
│  │    role     │     │    entity_id│     │    status   │     │    loss_date ││
│  │    active   │     │    field_   │     │    insured_ │     │    FK: policy││
│  │             │     │    name     │     │    name     │     │              ││
│  │             │     │    old_value│     │    ssn_tin  │     │              ││
│  │             │     │    new_value│     │    city     │     │              ││
│  │             │     │    user_id  │     │    state    │     │              ││
│  │             │     │    correla- │     │    zip      │     │              ││
│  │             │     │    tion_id  │     │    effective│     │              ││
│  └─────────────┘     │    created_ │     │    expiry   │     │              ││
│                      │    at       │     │             │     │              ││
│                      └─────────────┘     └─────────────┘     └──────────────┘│
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                          POLICY RELATED ENTITIES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │  Vehicle    │     │  Location   │     │  Coverage   │                   │
│  │             │     │             │     │             │                   │
│  │ PK: id      │     │ PK: id      │     │ PK: id      │                   │
│  │    year     │     │    address  │     │    type     │                   │
│  │    make     │     │    city     │     │    limit    │                   │
│  │    model    │     │    state    │     │    deductible│                  │
│  │    vin      │     │    zip      │     │    FK: policy│                  │
│  │    FK: policy│    │    FK: policy│    │             │                   │
│  └─────────────┘     └─────────────┘     └─────────────┘                   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                          CLAIM RELATED ENTITIES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐     ┌─────────────┐                                  │
│  │ ClaimPolicyOver- │     │  Reserve    │                                  │
│  │ ride             │     │             │                                  │
│  │                  │     │ PK: id      │                                  │
│  │ PK: id           │     │    type     │                                  │
│  │    field_name    │     │    amount   │                                  │
│  │    original_     │     │    balance  │                                  │
│  │    value         │     │    FK: claim│                                  │
│  │    override_     │     │             │                                  │
│  │    value         │     │             │                                  │
│  │    FK: claim     │     │             │                                  │
│  └──────────────────┘     └─────────────┘                                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                          PAYMENT ENTITIES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌──────────────┐                  │
│  │   Payment   │────►│    Payee    │────►│ PaymentMethod│                  │
│  │             │     │             │     │              │                  │
│  │ PK: id      │     │ PK: id      │     │ PK: id       │                  │
│  │    amount   │     │    name     │     │    type      │                  │
│  │    status   │     │    type     │     │    details   │                  │
│  │    method   │     │    tax_id   │     │    FK: payee │                  │
│  │    FK: claim│     │    address  │     │              │                  │
│  │    reference│     │    city     │     │              │                  │
│  │    processed│     │    state    │     │              │                  │
│  │    _at      │     │    zip      │     │              │                  │
│  └─────────────┘     │    phone    │     │              │                  │
│          │           │    email    │     │              │                  │
│          │           └─────────────┘     └──────────────┘                  │
│          │                                                                 │
│          ▼                                                                 │
│  ┌─────────────┐     ┌─────────────┐                                       │
│  │PaymentPayee │     │PaymentReserve│                                      │
│  │             │     │Allocation   │                                       │
│  │ PK: payment │     │             │                                       │
│  │    _id      │     │ PK: payment │                                       │
│  │    payee_id │     │    _id      │                                       │
│  │    amount   │     │    reserve  │                                       │
│  │    portion  │     │    _id      │                                       │
│  │             │     │    amount   │                                       │
│  └─────────────┘     │    is_eroding│                                      │
│                      └─────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Table Definitions

### Core Tables

#### users
Primary table for authentication and authorization.
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'AGENT', 'ADJUSTER', 'VIEWER')),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

#### policies
Central policy management table with encrypted sensitive data.
```sql
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE', 'EXPIRED', 'CANCELLED', 'SUSPENDED')),
    insured_first_name VARCHAR(100) NOT NULL,
    insured_last_name VARCHAR(100) NOT NULL,
    organizational_name VARCHAR(200),
    ssn_tin_encrypted TEXT, -- Fernet encrypted
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    loss_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL -- Optimistic locking
);
```

#### claims
Claims linked to policies with status tracking and business logic.
```sql
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number VARCHAR(50) UNIQUE NOT NULL,
    policy_id UUID NOT NULL REFERENCES policies(id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('OPEN', 'CLOSED', 'PAID', 'DENIED', 'PENDING')),
    loss_date DATE NOT NULL,
    reported_date DATE NOT NULL,
    description TEXT,
    adjuster_notes TEXT,
    is_subrogation BOOLEAN DEFAULT false NOT NULL,
    injury_incident BOOLEAN DEFAULT false NOT NULL,
    carrier_involvement JSONB, -- Structured carrier information
    coding_information JSONB, -- Claims coding data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL
);
```

#### vehicles
Vehicle information associated with policies.
```sql
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    vin VARCHAR(17) UNIQUE,
    license_plate VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

#### locations
Location/property information for policies.
```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    property_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

#### coverages
Coverage details for policies with limits and deductibles.
```sql
CREATE TABLE coverages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,
    limit_amount DECIMAL(15,2) NOT NULL,
    deductible_amount DECIMAL(15,2) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### Payment Tables

#### payees
Payee information for payments with KYC data.
```sql
CREATE TABLE payees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('INDIVIDUAL', 'BUSINESS', 'VENDOR')),
    tax_id_encrypted TEXT, -- Fernet encrypted SSN/EIN
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    kyc_verified BOOLEAN DEFAULT false NOT NULL,
    kyc_verified_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

#### payment_methods
Payment method details for payees.
```sql
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payee_id UUID NOT NULL REFERENCES payees(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('ACH', 'WIRE', 'CARD', 'CHECK')),
    details JSONB NOT NULL, -- Bank routing, account numbers (encrypted)
    is_verified BOOLEAN DEFAULT false NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

#### payments
Core payment transactions with lifecycle management.
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id),
    amount DECIMAL(15,2) NOT NULL, -- Can be positive, negative, or zero
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'PROCESSED', 'FAILED', 'VOIDED', 'REVERSED')),
    method VARCHAR(20) NOT NULL CHECK (method IN ('ACH', 'WIRE', 'CARD', 'CHECK', 'STRIPE')),
    reference_number VARCHAR(100),
    external_transaction_id VARCHAR(100),
    processed_at TIMESTAMP WITH TIME ZONE,
    void_reason TEXT,
    voided_at TIMESTAMP WITH TIME ZONE,
    voided_by_user_id UUID REFERENCES users(id),
    parent_payment_id UUID REFERENCES payments(id), -- For reversals/corrections
    is_tax_reportable BOOLEAN DEFAULT false NOT NULL,
    withholding_amount DECIMAL(15,2) DEFAULT 0 NOT NULL,
    memo TEXT,
    documents JSONB, -- Array of document references
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL
);
```

#### payment_payees
Junction table for payments with multiple payees.
```sql
CREATE TABLE payment_payees (
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    payee_id UUID NOT NULL REFERENCES payees(id),
    amount DECIMAL(15,2) NOT NULL,
    portion DECIMAL(5,4) NOT NULL, -- Percentage as decimal (0.25 = 25%)
    payment_method_id UUID NOT NULL REFERENCES payment_methods(id),
    is_joint BOOLEAN DEFAULT false NOT NULL, -- Joint payee designation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (payment_id, payee_id)
);
```

#### reserves
Reserve lines for claims with balance tracking.
```sql
CREATE TABLE reserves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'MEDICAL', 'PROPERTY', 'LIABILITY', etc.
    initial_amount DECIMAL(15,2) NOT NULL,
    current_balance DECIMAL(15,2) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

#### payment_reserve_allocations
Payment allocation across reserve lines.
```sql
CREATE TABLE payment_reserve_allocations (
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    reserve_id UUID NOT NULL REFERENCES reserves(id),
    amount DECIMAL(15,2) NOT NULL,
    is_eroding BOOLEAN DEFAULT true NOT NULL, -- Whether payment reduces reserve balance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (payment_id, reserve_id)
);
```

### Audit and Claim Override Tables

#### claim_policy_overrides
Claim-level policy data overrides with change tracking.
```sql
CREATE TABLE claim_policy_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    original_value TEXT,
    override_value TEXT NOT NULL,
    reason TEXT,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (claim_id, field_name)
);
```

#### audit_logs
Comprehensive audit trail for all data changes.
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'User', 'Policy', 'Claim', 'Payment'
    entity_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    user_id UUID REFERENCES users(id),
    correlation_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

## Indexes for Performance Optimization

### Primary Search Indexes
```sql
-- Policy search optimization
CREATE INDEX idx_policies_search ON policies (
    insured_first_name, insured_last_name, number, type, city, state, zip_code
);

-- Policy number lookup (most common search)
CREATE UNIQUE INDEX idx_policies_number ON policies (number);

-- SSN/TIN search (encrypted field, will need application-level handling)
CREATE INDEX idx_policies_ssn_tin ON policies (ssn_tin_encrypted);

-- Claims by policy and status
CREATE INDEX idx_claims_policy_status ON claims (policy_id, status, loss_date DESC);

-- Claims by date range
CREATE INDEX idx_claims_loss_date ON claims (loss_date DESC);

-- Payments by claim and status
CREATE INDEX idx_payments_claim_status ON payments (claim_id, status, created_at DESC);

-- Audit trail by entity
CREATE INDEX idx_audit_logs_entity ON audit_logs (entity_type, entity_id, created_at DESC);

-- User lookup by email (authentication)
CREATE UNIQUE INDEX idx_users_email ON users (email);
```

### Relationship Indexes
```sql
-- Foreign key indexes for better JOIN performance
CREATE INDEX idx_vehicles_policy_id ON vehicles (policy_id);
CREATE INDEX idx_locations_policy_id ON locations (policy_id);
CREATE INDEX idx_coverages_policy_id ON coverages (policy_id);
CREATE INDEX idx_claims_policy_id ON claims (policy_id);
CREATE INDEX idx_reserves_claim_id ON reserves (claim_id);
CREATE INDEX idx_payments_claim_id ON payments (claim_id);
CREATE INDEX idx_payment_methods_payee_id ON payment_methods (payee_id);
```

### Performance Monitoring Indexes
```sql
-- Composite indexes for complex queries
CREATE INDEX idx_policies_full_search ON policies (
    status, type, state, effective_date, expiry_date
) WHERE status = 'ACTIVE';

CREATE INDEX idx_claims_recent_by_status ON claims (
    status, loss_date DESC, created_at DESC
) WHERE created_at >= CURRENT_DATE - INTERVAL '1 year';
```

## Constraints and Data Integrity

### Check Constraints
- User roles limited to defined enum values
- Policy and claim statuses restricted to valid values
- Payment amounts can be positive, negative, or zero
- Payment method types restricted to supported types
- Percentage portions in payment_payees must be between 0 and 1

### Foreign Key Constraints
- All relationships properly constrained with cascading deletes where appropriate
- Audit logs reference users but allow NULL for system operations
- Payment reversals reference parent payments

### Unique Constraints
- Policy numbers must be unique across the system
- Claim numbers must be unique across the system
- User emails must be unique
- VINs must be unique where provided

### Business Rule Constraints
- Policy effective_date must be <= expiry_date
- Claim loss_date must be within policy effective period
- Payment reserve allocations cannot exceed available balance (enforced in application layer)
- Payee portions in multi-payee payments must sum to 1.0 (enforced in application layer)

## Data Security and Encryption

### Encrypted Fields
- `policies.ssn_tin_encrypted` - Fernet encryption for SSN/TIN data
- `payees.tax_id_encrypted` - Fernet encryption for tax identification
- `payment_methods.details` - Bank account and routing numbers encrypted

### Data Masking Strategy
- SSN/TIN displayed as ***-**-1234 (last 4 digits only)
- Bank account numbers displayed as ****1234 (last 4 digits only)
- Credit card numbers follow PCI-DSS masking requirements

### Audit Trail Security
- All sensitive data changes logged with before/after values (encrypted)
- IP addresses and user agents tracked for security analysis
- Correlation IDs enable end-to-end request tracing

## Database Configuration

### Connection Settings
- **Production**: PostgreSQL 16 with asyncpg driver
- **Development**: SQLite with aiosqlite driver
- **Connection pooling**: 20 max connections, 5 min connections
- **Query timeout**: 30 seconds for long-running operations

### Performance Tuning
- `shared_buffers`: 25% of total RAM
- `effective_cache_size`: 75% of total RAM
- `work_mem`: 4MB for sorting operations
- `maintenance_work_mem`: 64MB for maintenance operations

### Backup Strategy
- Daily full backups with 30-day retention
- Hourly transaction log backups
- Point-in-time recovery capability
- Cross-region backup replication for disaster recovery

This database design supports all functional requirements while maintaining ACID compliance, data security, and query performance optimization for the integrated policy, claims, and payments platform.