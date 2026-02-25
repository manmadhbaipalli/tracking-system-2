# Database Architecture: auh-sys (Integrated Policy, Claims, and Payments Platform)

## Overview
This document defines the database schema and entity relationships for the auh-sys insurance platform. The system manages the complete lifecycle of insurance policies, claims processing, and payment/disbursement workflows.

## Technology Stack
- **Language:** Python 3.12
- **Framework:** FastAPI (async)
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL 16 (production), SQLite 3 (development)
- **Async/Sync:** Sync (SQLAlchemy with standard engine)
- **Migration Tool:** Alembic

## Core Entities

### Authentication & Authorization
- **User**: Platform users with role-based access control
- **Role**: Predefined roles (AGENT, UNDERWRITER, CLAIMS_ADJUSTER, FINANCE_MANAGER, RECOVERY_MANAGER, ADMIN, AUDITOR)
- **Permission**: Fine-grained permissions linked to roles
- **AuditLog**: Audit trail for all actions (user, timestamp, action, entity, changes)

### Policy Management
- **Policy**: Insurance policies with lifecycle management
- **Coverage**: Coverage types, limits, deductibles linked to policies
- **Vehicle**: Vehicle details (year, make, model, VIN)
- **Location**: Address details (city, state, zip)
- **Insured**: Party information (name, SSN/TIN, contact)
- **Endorsement**: Policy modifications/endorsements

### Claims Management
- **Claim**: Claims linked to policies with full lifecycle support
- **ClaimAdjustment**: Adjustments/updates to claim values
- **ReserveLine**: Reserve allocations for claims
- **ClaimLevelPolicy**: Claim-specific policy data (when policy is unverified)
- **OtherCarrierInfo**: Other carrier party and payment info for claims

### Payments & Disbursements
- **Payment**: Payment transactions linked to claims/policies
- **PaymentMethod**: Payment method types (ACH, WIRE, CARD, STRIPE, GLOBAL_PAYOUTS)
- **Payee**: Vendor/claimant onboarding with KYC verification
- **PaymentDetail**: Line items for payment transactions
- **PaymentDeduction**: Tax witholding and deductions
- **PaymentDocument**: Document attachments to payments
- **ScheduledPayment**: Subrogation scheduled payment tracking

### Integration & Utility
- **ExternalEstimate**: Payable line items from Xactimate/XactAnalysis
- **PaymentRoutingRule**: Business rules for payment routing
- **TaxReportablePayment**: Tax reporting details for payments

## Entity Relationships (Simplified ER)

```
┌──────────────┐
│    Users     │
└──────────────┘
      │ 1:N
      ├──────────────────────────────────────┐
      │                                      │
      ▼                                      ▼
┌──────────────┐                    ┌──────────────────┐
│   Policies   │◄──────┐            │  AuditLog        │
└──────────────┘       │            └──────────────────┘
      │ 1:N            │
      │                │ N:1
      ▼                │
┌──────────────┐       │
│   Coverage   │       │
└──────────────┘       │
                       │
┌──────────────┐       │
│   Claims ────┼───────┘
└──────────────┘
      │ 1:N
      ├──────────────┬──────────────────────┐
      │              │                      │
      ▼              ▼                      ▼
┌────────────────┐ ┌──────────────┐ ┌────────────────────┐
│ ReserveLine    │ │ Payments     │ │ ClaimLevelPolicy   │
└────────────────┘ └──────────────┘ └────────────────────┘
                        │ 1:N
                        ├──────────────┬──────────────────┐
                        │              │                  │
                        ▼              ▼                  ▼
                  ┌────────────────┐ ┌───────────┐ ┌────────────────┐
                  │ PaymentDetail  │ │ Payee     │ │ PaymentDocument│
                  └────────────────┘ └───────────┘ └────────────────┘
                                            │ 1:N
                                            ▼
                                    ┌────────────────┐
                                    │PaymentDeduction│
                                    └────────────────┘
```

## Table Design Summary

| Entity | Purpose | Key Audit Cols |
|--------|---------|----------------|
| users | Authentication & authorization | created_at, updated_at |
| roles | Role definitions | created_at, updated_at |
| policies | Insurance policies | created_at, updated_at |
| claims | Claim records linked to policies | created_at, updated_at |
| payments | Payment transactions | created_at, updated_at |
| payees | Vendor/claimant information | created_at, updated_at |
| reserve_lines | Claim reserve allocations | created_at, updated_at |
| audit_logs | Comprehensive audit trail | created_at |

## Design Decisions

1. **Audit Mixin (MANDATORY)**: All entities inherit from `AuditMixin` with `id`, `created_at`, `updated_at`
2. **Soft Deletes**: No soft delete columns; hard delete with audit trail for recovery
3. **Timestamps**: UTC timezone-aware, server-side defaults via `func.now()`
4. **Enums**: Python enums with SQLAlchemy Enum type
5. **Relationships**: Bidirectional with `relationship()` and `back_populates`
6. **PII Masking**: SSN/TIN stored encrypted, masking in application layer
7. **Cascading**: Parent-child relationships use `cascade="all, delete-orphan"`
8. **Indexing**: Foreign keys and frequently-searched columns indexed
9. **Type Safety**: SQLAlchemy 2.0 style with `Mapped[T]` annotations

## Dependencies
- sqlalchemy>=2.0
- alembic>=1.13.0
- pydantic-settings>=2.0
- python-jose[cryptography]
- passlib[bcrypt]
- structlog
- uvicorn
- fastapi

