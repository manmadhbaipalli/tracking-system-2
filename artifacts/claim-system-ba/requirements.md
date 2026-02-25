# Insurance Platform Requirements

## Functional Requirements

### Access & Authentication
- Only authorized users with appropriate roles can access policy, claims, and payment modules
- All actions (search, create, edit, payment, claim) must be logged with user ID and timestamp for audit purposes

### Policy Management
1. Support creation, retrieval, update, and search of policies
2. Policy search must allow searching by Policy Number, Insured First Name, Insured Last Name, Policy Type, Loss Date, Policy City, Policy State, Policy Zip, SSN/TIN, and Organizational Name
3. Support both exact and partial matches for name, policy number, and address
4. Display policy details including: Insured Name, Policy Number, Policy Type, Effective Date, Expiration Date, Policy Status, Vehicle Details, Location Details, Coverage Details
5. SSN/TIN must be masked according to security policies
6. Allow users to reset all defined search criteria to default/empty values
7. Policy details must be accessible and compliant with WCAG guidelines
8. All policy actions must be auditable

### Claims Management
1. Claims must be linked to policies and support creation, retrieval, update, and search
2. Claim History must display a list of past claims associated with the policy
3. Claims must be sorted by Date of Loss (most recent first) and filterable by Claim Status
4. Add/Edit policy information at claim level when policy is unverified; changes must be tracked separately
5. Visual indicator must show when claim-level policy information is being used
6. Audit log must track all changes to claim-level policy data
7. Claims must support referral to subrogation and management of scheduled payments
8. Claims must support injury incident details, coding information, and carrier involvement

### Payments & Disbursements
1. Payments must be linked to claims and policies, supporting multiple payment methods
2. Support onboarding of vendors and claimants with secure payment method verification
3. Enable automated creation of payable line items from external estimates
4. Allow configuration of payment routing rules based on payee, payment type, and business rules
5. Provide full payment lifecycle management: creation, voids, reversals, reissues, reserve handling
6. Enable allocation of payments across multiple reserve lines and management of joint payees
7. Support creation of Electronic Funds Transfers (EFT) and wire transfers
8. Allow creation of payments with positive, negative, or zero dollar amounts
9. Support designation of payments as eroding or non-eroding against reserve lines
10. Enable management of multiple payment details per transaction
11. Allow withholding of income tax and designation of payments as tax reportable
12. Support document attachment to payment transactions
13. Remittance & Medical Payments: Support EDI/EOB-style remittances to medical providers
14. Negotiation & Settlement Management: Provide negotiation management, coverage opinion requests, and settlement plan tracking
15. Compliance: Ensure PCI-DSS compliance, mask sensitive payment information, encrypt all payment data

### Integration Requirements
1. Integrate policy, claims, and payment modules for seamless workflow
2. Integrate with external systems: Stripe Connect, Global Payouts, Bank ACH/Wire, Xactimate/XactAnalysis, Accounting, Bill Review, EDI 835/837, Litigation Data, Tax ID, General Ledger, Agency Markets Payment Service, Document Management
3. Capture and reuse Other Carrier Information across claim functions

## Non-Functional Requirements

### Performance
- Policy search results must be returned within 3 seconds
- Policy details and claim history within 5 seconds
- Payment processing within 5 seconds
- System must support concurrent user sessions without performance degradation
- All integrations must be robust and support error handling and retry logic

### Security
- Mask and encrypt sensitive data (SSN/TIN, payment info)
- Enforce role-based access control
- Maintain comprehensive audit logs for all actions

### Regulatory Compliance
- 7-year data retention for policy records
- 30-day cancellation notice requirement
- Comply with state privacy regulations
- Support annual reporting obligations

### Reliability
- 99.9% uptime for policy and claims services
- Transaction integrity for payments and claim settlements
- Idempotent API operations for payment processing

## Error Handling & Messaging
1. If no matching policies or claims are found, display: "No matching policies/claims found."
2. If the system is unavailable, display: "System is currently unavailable."
3. If policy/claim/payment details cannot be retrieved, display: "Unable to retrieve details. Please try again later."
4. If claim-level policy data cannot be saved, display: "Unable to save claim-level policy data. Please try again later."
5. If no prior claims exist, display: "No prior claims exist for this policy."

## ACORD Domain Model

### Policy
- policy_number: String (unique, format: POL-YYYY-NNNNNN)
- insured_id: FK -> Policyholder
- policy_type: Enum (AUTO, HOME, LIFE, HEALTH, COMMERCIAL)
- status: Enum (QUOTED, BOUND, ISSUED, ACTIVE, CANCELLED, EXPIRED)
- effective_date: Date
- expiration_date: Date
- aggregate_limit: Decimal
- total_premium: Decimal (calculated)

### Policyholder (Insured Party)
- policyholder_id: String (unique)
- type: Enum (INDIVIDUAL, BUSINESS)
- first_name: String (required for INDIVIDUAL)
- last_name: String (required for INDIVIDUAL)
- company_name: String (required for BUSINESS)
- date_of_birth: Date (required for INDIVIDUAL)
- tax_id: String (SSN or EIN)

### Coverage
- coverage_code: String (ACORD coverage code)
- coverage_type: Enum (LIABILITY, COLLISION, COMPREHENSIVE, MEDICAL, etc.)
- limit_amount: Decimal
- deductible_amount: Decimal
- premium_portion: Decimal

### Claim
- claim_number: String (unique, format: CLM-YYYY-NNNNNN)
- policy_id: FK -> Policy
- status: Enum (FNOL, UNDER_REVIEW, APPROVED, DENIED, SETTLED, CLOSED)
- date_of_loss: Date
- reported_date: Date
- loss_type: Enum (COLLISION, THEFT, FIRE, WATER, LIABILITY, etc.)
- reserve_amount: Decimal
- paid_amount: Decimal

### Endorsement
- endorsement_number: String (unique)
- policy_id: FK -> Policy
- type: Enum (ADD_COVERAGE, REMOVE_COVERAGE, CHANGE_LIMIT, ADD_DRIVER, etc.)
- effective_date: Date
- premium_change: Decimal

### Underwriting
- risk_score: Integer (1-100)
- decision: Enum (APPROVE, DECLINE, REFER)
- conditions: List[String]
- rating_factors: JSON