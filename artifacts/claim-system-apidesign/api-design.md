# API Design - Integrated Policy, Claims, and Payments Platform

## API Architecture Overview

### Base Configuration
- **Base URL**: `/api/v1`
- **Content Type**: `application/json`
- **Authentication**: JWT Bearer tokens in Authorization header
- **API Versioning**: URL-based versioning (v1, v2, etc.)
- **Default Pagination**: 20 items per page, maximum 100 items per page

### Response Format Standards

#### Success Responses
All successful list responses use a consistent pagination envelope:
```json
{
  "items": [...],
  "page": 1,
  "size": 20,
  "total": 150,
  "pages": 8,
  "has_next": true,
  "has_prev": false
}
```

#### Error Response Format
All error responses follow a consistent structure with correlation IDs:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for request data",
    "details": {
      "field": "email",
      "message": "Invalid email format"
    },
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Data Masking and Security

#### SSN/TIN Masking
- Display format: `***-**-1234` (last 4 digits only)
- All API responses must mask sensitive personal identifiers

#### Payment Information Masking
- Bank account: `****1234` (last 4 digits only)
- Credit card: Follow PCI-DSS masking requirements

## Endpoint Specifications

### Authentication Module (`/auth`)

#### POST `/auth/login`
**Purpose**: Authenticate user and return JWT token
**Request Schema**:
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```
**Response Schema**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "AGENT",
    "is_active": true
  }
}
```

#### POST `/auth/register`
**Purpose**: Register new user account
**Request Schema**:
```json
{
  "email": "newuser@example.com",
  "password": "securePassword123",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "VIEWER"
}
```

#### POST `/auth/refresh`
**Purpose**: Refresh access token using refresh token
**Request Schema**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### User Management Module (`/users`)

#### GET `/users/me`
**Purpose**: Get current user profile
**Authentication**: Required
**Response Schema**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "AGENT",
  "is_active": true,
  "last_login": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### PUT `/users/me`
**Purpose**: Update current user profile
**Request Schema**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com"
}
```

#### GET `/users/{id}`
**Purpose**: Get user by ID (Admin only)
**Authorization**: ADMIN role required

#### POST `/users`
**Purpose**: Create new user (Admin only)
**Authorization**: ADMIN role required

#### DELETE `/users/{id}`
**Purpose**: Deactivate user (Admin only)
**Authorization**: ADMIN role required

### Policy Management Module (`/policies`)

#### GET `/policies/search`
**Purpose**: Search policies with comprehensive criteria
**Query Parameters**:
- `policy_number`: Exact or partial match
- `insured_first_name`: Partial match, case-insensitive
- `insured_last_name`: Partial match, case-insensitive
- `policy_type`: Exact match
- `loss_date`: Date range (YYYY-MM-DD)
- `loss_date_from`: Start date for range
- `loss_date_to`: End date for range
- `city`: Partial match, case-insensitive
- `state`: Exact match (2-letter code)
- `zip_code`: Exact or partial match
- `ssn_tin`: Last 4 digits only (encrypted search)
- `organizational_name`: Partial match, case-insensitive
- `status`: Policy status filter
- `page`: Page number (default: 1)
- `size`: Items per page (default: 20, max: 100)

**Response Schema**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "number": "POL-2024-001",
      "type": "AUTO",
      "status": "ACTIVE",
      "insured_name": "John Doe",
      "organizational_name": null,
      "ssn_tin_masked": "***-**-1234",
      "city": "New York",
      "state": "NY",
      "zip_code": "10001",
      "effective_date": "2024-01-01",
      "expiry_date": "2024-12-31",
      "loss_date": "2024-06-15",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "page": 1,
  "size": 20,
  "total": 150,
  "pages": 8,
  "has_next": true,
  "has_prev": false
}
```

#### GET `/policies/{id}`
**Purpose**: Get detailed policy information with relationships
**Response Schema**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "number": "POL-2024-001",
  "type": "AUTO",
  "status": "ACTIVE",
  "insured_first_name": "John",
  "insured_last_name": "Doe",
  "organizational_name": null,
  "ssn_tin_masked": "***-**-1234",
  "city": "New York",
  "state": "NY",
  "zip_code": "10001",
  "effective_date": "2024-01-01",
  "expiry_date": "2024-12-31",
  "loss_date": "2024-06-15",
  "vehicles": [
    {
      "id": "vehicle-id-1",
      "year": 2022,
      "make": "Toyota",
      "model": "Camry",
      "vin": "1HGBH41JXMN109186",
      "license_plate": "ABC123"
    }
  ],
  "locations": [
    {
      "id": "location-id-1",
      "address": "123 Main St",
      "city": "New York",
      "state": "NY",
      "zip_code": "10001",
      "property_type": "RESIDENTIAL"
    }
  ],
  "coverages": [
    {
      "id": "coverage-id-1",
      "type": "LIABILITY",
      "limit_amount": 100000.00,
      "deductible_amount": 500.00,
      "is_active": true
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "version": 1
}
```

#### POST `/policies`
**Purpose**: Create new policy
**Authorization**: AGENT or ADMIN role required
**Request Schema**:
```json
{
  "number": "POL-2024-002",
  "type": "AUTO",
  "status": "ACTIVE",
  "insured_first_name": "Jane",
  "insured_last_name": "Smith",
  "organizational_name": null,
  "ssn_tin": "123-45-6789",
  "city": "Los Angeles",
  "state": "CA",
  "zip_code": "90210",
  "effective_date": "2024-02-01",
  "expiry_date": "2025-01-31",
  "vehicles": [...],
  "locations": [...],
  "coverages": [...]
}
```

#### PUT `/policies/{id}`
**Purpose**: Update existing policy
**Authorization**: AGENT or ADMIN role required

#### DELETE `/policies/{id}`
**Purpose**: Soft delete policy (set status to CANCELLED)
**Authorization**: ADMIN role required

### Claims Management Module (`/claims`)

#### GET `/claims/{id}`
**Purpose**: Get detailed claim information
**Response Schema**:
```json
{
  "id": "claim-id-1",
  "number": "CLM-2024-001",
  "policy_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "OPEN",
  "loss_date": "2024-06-15",
  "reported_date": "2024-06-16",
  "description": "Vehicle collision on Main St",
  "adjuster_notes": "Initial assessment completed",
  "is_subrogation": false,
  "injury_incident": false,
  "carrier_involvement": {},
  "coding_information": {},
  "policy_overrides": [
    {
      "field_name": "insured_address",
      "original_value": "123 Main St",
      "override_value": "456 Oak Ave",
      "reason": "Address correction per claim investigation"
    }
  ],
  "reserves": [
    {
      "id": "reserve-id-1",
      "type": "PROPERTY",
      "initial_amount": 50000.00,
      "current_balance": 35000.00,
      "is_active": true
    }
  ],
  "created_at": "2024-06-16T09:00:00Z",
  "updated_at": "2024-06-20T14:30:00Z",
  "version": 3
}
```

#### POST `/claims`
**Purpose**: Create new claim
**Authorization**: ADJUSTER or ADMIN role required
**Request Schema**:
```json
{
  "number": "CLM-2024-002",
  "policy_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "OPEN",
  "loss_date": "2024-07-01",
  "reported_date": "2024-07-02",
  "description": "Property damage due to storm",
  "is_subrogation": false,
  "injury_incident": false
}
```

#### PUT `/claims/{id}`
**Purpose**: Update claim information
**Authorization**: ADJUSTER or ADMIN role required

#### PUT `/claims/{id}/status`
**Purpose**: Update claim status with workflow validation
**Request Schema**:
```json
{
  "status": "CLOSED",
  "reason": "Settlement completed",
  "adjuster_notes": "Final settlement paid to all parties"
}
```

#### GET `/policies/{id}/claims`
**Purpose**: Get claim history for a policy
**Query Parameters**:
- `status`: Filter by claim status
- `page`: Page number
- `size`: Items per page

**Response Schema**:
```json
{
  "items": [
    {
      "id": "claim-id-1",
      "number": "CLM-2024-001",
      "status": "PAID",
      "loss_date": "2024-06-15",
      "reported_date": "2024-06-16",
      "description": "Vehicle collision on Main St"
    }
  ],
  "page": 1,
  "size": 20,
  "total": 3,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### Payment Processing Module (`/payments`)

#### GET `/payments/{id}`
**Purpose**: Get detailed payment information
**Response Schema**:
```json
{
  "id": "payment-id-1",
  "claim_id": "claim-id-1",
  "amount": 15000.00,
  "status": "PROCESSED",
  "method": "ACH",
  "reference_number": "PAY-2024-001",
  "external_transaction_id": "ext-txn-123",
  "processed_at": "2024-06-25T10:00:00Z",
  "is_tax_reportable": true,
  "withholding_amount": 1500.00,
  "memo": "Property damage settlement",
  "payees": [
    {
      "id": "payee-id-1",
      "name": "John Doe",
      "type": "INDIVIDUAL",
      "amount": 10000.00,
      "portion": 0.6667,
      "is_joint": false,
      "payment_method": {
        "type": "ACH",
        "details": {
          "bank_name": "First National Bank",
          "account_type": "CHECKING",
          "account_number_masked": "****1234"
        }
      }
    }
  ],
  "reserve_allocations": [
    {
      "reserve_id": "reserve-id-1",
      "amount": 15000.00,
      "is_eroding": true
    }
  ],
  "documents": [],
  "created_at": "2024-06-25T09:00:00Z",
  "updated_at": "2024-06-25T10:00:00Z",
  "version": 2
}
```

#### POST `/payments`
**Purpose**: Create new payment
**Authorization**: ADJUSTER or ADMIN role required
**Request Schema**:
```json
{
  "claim_id": "claim-id-1",
  "amount": 15000.00,
  "method": "ACH",
  "memo": "Property damage settlement",
  "is_tax_reportable": true,
  "withholding_amount": 1500.00,
  "payees": [
    {
      "payee_id": "payee-id-1",
      "amount": 10000.00,
      "portion": 0.6667,
      "payment_method_id": "pm-id-1",
      "is_joint": false
    }
  ],
  "reserve_allocations": [
    {
      "reserve_id": "reserve-id-1",
      "amount": 15000.00,
      "is_eroding": true
    }
  ]
}
```

#### PUT `/payments/{id}/void`
**Purpose**: Void a payment
**Request Schema**:
```json
{
  "reason": "Incorrect amount - reissue required"
}
```

#### POST `/payments/{id}/reverse`
**Purpose**: Create reversal payment
**Request Schema**:
```json
{
  "reason": "Overpayment correction",
  "amount": 5000.00
}
```

#### GET `/claims/{id}/payments`
**Purpose**: Get payment history for a claim
**Response**: Paginated list of payments

### Health Check Module (`/health`)

#### GET `/health/live`
**Purpose**: Liveness probe for container orchestration
**Response Schema**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### GET `/health/ready`
**Purpose**: Readiness probe with dependency checks
**Response Schema**:
```json
{
  "status": "ready",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "external_services": "healthy"
  },
  "version": "1.0.0"
}
```

## Error Codes and Messages

### Authentication Errors
- `AUTH_INVALID_CREDENTIALS`: "Invalid email or password"
- `AUTH_TOKEN_EXPIRED`: "Access token has expired"
- `AUTH_TOKEN_INVALID`: "Invalid or malformed token"
- `AUTH_INSUFFICIENT_PRIVILEGES`: "Insufficient privileges for this operation"
- `AUTH_ACCOUNT_LOCKED`: "Account is temporarily locked due to failed login attempts"

### Validation Errors
- `VALIDATION_ERROR`: "Request validation failed"
- `VALIDATION_REQUIRED_FIELD`: "Required field is missing: {field}"
- `VALIDATION_INVALID_FORMAT`: "Invalid format for field: {field}"
- `VALIDATION_VALUE_OUT_OF_RANGE`: "Value out of acceptable range for field: {field}"

### Business Logic Errors
- `POLICY_NOT_FOUND`: "Policy not found"
- `POLICY_EXPIRED`: "Policy has expired"
- `CLAIM_NOT_FOUND`: "Claim not found"
- `CLAIM_STATUS_INVALID`: "Invalid status transition"
- `PAYMENT_INSUFFICIENT_RESERVES`: "Insufficient reserves for payment amount"
- `PAYMENT_ALREADY_PROCESSED`: "Payment has already been processed"

### System Errors
- `SYSTEM_UNAVAILABLE`: "System is currently unavailable"
- `DATABASE_ERROR`: "Database operation failed"
- `EXTERNAL_SERVICE_ERROR`: "External service integration failed"
- `RATE_LIMIT_EXCEEDED`: "API rate limit exceeded"

## Security and Compliance

### Authentication Flow
1. Client sends credentials to `/auth/login`
2. Server validates credentials and returns JWT access/refresh tokens
3. Client includes access token in Authorization header for subsequent requests
4. Server validates token and extracts user context for request processing

### Role-Based Access Control
- **ADMIN**: Full system access, user management
- **AGENT**: Policy management, view claims and payments
- **ADJUSTER**: Claim and payment processing, policy viewing
- **VIEWER**: Read-only access to assigned records

### Audit Trail Requirements
All API operations must log:
- User ID and role
- Timestamp (UTC)
- IP address and user agent
- Correlation ID for request tracing
- Entity ID and operation type
- Field-level changes (before/after values for updates)

### Rate Limiting
- Anonymous endpoints: 100 requests/hour per IP
- Authenticated endpoints: 1000 requests/hour per user
- Search endpoints: 200 requests/hour per user
- Payment endpoints: 50 requests/hour per user

### Data Validation Rules
- All UUIDs must be valid format
- Dates must be in ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
- Monetary amounts must have maximum 2 decimal places
- Email addresses must follow RFC 5322 standard
- Password complexity: minimum 8 characters, mixed case, numbers, special characters

This API design provides a comprehensive, secure, and scalable foundation for the integrated policy, claims, and payments platform while maintaining consistency with industry standards and regulatory requirements.