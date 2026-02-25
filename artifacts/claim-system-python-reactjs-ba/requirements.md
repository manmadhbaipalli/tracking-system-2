# ACORD Insurance Platform Requirements
## Integrated Policy, Claims, and Payments Management System

**Document Date:** 2026-02-24
**Project:** claim-system-python-reactjs
**Phase:** Business Analysis

---

## 1. Executive Summary

This document specifies functional, non-functional, security, and regulatory requirements for a unified **insurance platform** supporting comprehensive ACORD-compliant policy lifecycle management, claims processing, and payment disbursement workflows. The platform integrates policy administration, claims management, and payment handling with robust audit trails, security controls, and regulatory compliance.

---

## 2. User Stories

### Policy Management

#### US-001: Policy Quote Creation
**As an** Insurance Agent
**I want to** create a quote for a prospective Insured
**So that** I can provide a premium estimate before binding
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-001.1: Agent selects Policy Type (AUTO, HOME, LIFE, HEALTH, COMMERCIAL)
- AC-001.2: Agent enters Insured details (full name, date of birth, address, SSN/TIN)
- AC-001.3: Agent selects Coverage types with Limits and Deductibles
- AC-001.4: System calculates total premium using rating engine (Base Rate × Territory Factor × Age Factor × Claims Factor)
- AC-001.5: System generates Quote Number (QUO-YYYY-NNNNNN)
- AC-001.6: Quote is valid for 30 days from creation and can be converted to Binding
- AC-001.7: SSN/TIN is masked in UI display per PII rules

**Error Scenarios:**
- E-001.1: Coverage Limit exceeds Policy Aggregate Limit → 422 "Coverage limit cannot exceed policy aggregate"
- E-001.2: Insured fails eligibility check (age, occupation, location) → 422 "Insured fails eligibility criteria"
- E-001.3: Rating engine error → 500 with fallback to manual underwriting workflow
- E-001.4: Invalid address format → 400 "Address validation failed"

---

#### US-002: Policy Bind (Quote to Binding Conversion)
**As an** Insurance Agent
**I want to** bind a quote and create an Active Policy
**So that** coverage begins on the effective date
**Priority:** High | **Story Points:** 5

**Acceptance Criteria:**
- AC-002.1: Agent selects an existing Quote (not expired)
- AC-002.2: Agent sets Effective Date (today or future date)
- AC-002.3: System validates effective date >= today
- AC-002.4: System generates Policy Number (POL-YYYY-NNNNNN, auto-incremented)
- AC-002.5: Policy status transitions from QUOTED → BOUND
- AC-002.6: Premium payment terms are established
- AC-002.7: Binding is logged to audit trail with Agent ID and timestamp

**Error Scenarios:**
- E-002.1: Quote expired (> 30 days) → 400 "Quote has expired"
- E-002.2: Effective date in past → 422 "Effective date cannot be in the past"
- E-002.3: Premium payment fails → 402 "Payment required to bind policy"
- E-002.4: Policy with same details already exists → 409 "Policy already exists"

---

#### US-003: Policy Issuance
**As a** Underwriter
**I want to** approve and issue a Bound Policy
**So that** the Policyholder receives official policy documents
**Priority:** High | **Story Points:** 5

**Acceptance Criteria:**
- AC-003.1: Underwriter reviews BOUND policy
- AC-003.2: Underwriter approves policy or requests additional information
- AC-003.3: Policy status transitions from BOUND → ISSUED
- AC-003.4: System generates policy documents (declarations page, coverage pages, terms & conditions)
- AC-003.5: Policy documents are stored in document management system
- AC-003.6: Issuance is logged with Underwriter ID and approval reason
- AC-003.7: Policy moves to ACTIVE status on effective date

**Error Scenarios:**
- E-003.1: Missing required coverage information → 422 "Incomplete policy information"
- E-003.2: Document generation fails → 500 "Unable to generate policy documents"
- E-003.3: Underwriter lacks approval authority → 403 "Insufficient permissions"

---

#### US-004: Policy Search and Retrieval
**As a** Policyholder or Agent
**I want to** search for and view my policies
**So that** I can access policy details and manage my account
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-004.1: Search supports Policy Number, Insured First Name, Insured Last Name
- AC-004.2: Search supports Policy Type (AUTO, HOME, LIFE, HEALTH, COMMERCIAL)
- AC-004.3: Search supports Location criteria (City, State, Zip)
- AC-004.4: Search supports SSN/TIN (masked in query results)
- AC-004.5: Search supports exact and partial text matches (case-insensitive)
- AC-004.6: Search supports date range filters (Effective Date, Expiration Date)
- AC-004.7: Results returned within 3 seconds
- AC-004.8: Results are paginated (default 25 per page, max 100)
- AC-004.9: Reset search button clears all criteria
- AC-004.10: Search results display: Policy Number, Insured Name, Policy Type, Status, Effective Date, Expiration Date

**Error Scenarios:**
- E-004.1: Invalid search parameter format → 400 "Invalid search parameter"
- E-004.2: No matching policies found → 200 "No matching policies found"
- E-004.3: Search timeout (> 3 seconds) → 504 "Search request timed out"
- E-004.4: Unauthorized search attempt (RBAC violation) → 403 "Insufficient permissions"

---

#### US-005: Policy Detail View
**As a** Policyholder or Agent
**I want to** view complete policy details
**So that** I can understand my coverage and terms
**Priority:** High | **Story Points:** 5

**Acceptance Criteria:**
- AC-005.1: Display Insured Name, Policy Number, Policy Type, Status
- AC-005.2: Display Effective Date, Expiration Date, Aggregate Limit, Total Premium
- AC-005.3: Display Vehicle Details (Year, Make, Model, VIN for AUTO policies)
- AC-005.4: Display Location Details (Address, City, State, Zip for HOME policies)
- AC-005.5: Display all Coverages (Type, Limit, Deductible, Premium Portion)
- AC-005.6: SSN/TIN masked in display (last 4 digits visible only)
- AC-005.7: Display linked Endorsements and Claim History (linked data)
- AC-005.8: Page loads within 5 seconds
- AC-005.9: Page is WCAG AA compliant

**Error Scenarios:**
- E-005.1: Policy not found → 404 "Policy not found"
- E-005.2: User lacks view permission → 403 "Access denied"
- E-005.3: Data retrieval fails → 500 "Unable to retrieve policy details"

---

#### US-006: Policy Endorsement (Mid-Term Modification)
**As an** Agent or Policyholder
**I want to** add, modify, or remove coverages on an active policy
**So that** I can adjust coverage mid-term without renewing the entire policy
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-006.1: Endorsement can be created only on ACTIVE policies
- AC-006.2: Endorsement Effective Date must be within current policy period
- AC-006.3: Endorsement Type supported: ADD_COVERAGE, REMOVE_COVERAGE, CHANGE_LIMIT, INCREASE_LIMIT, DECREASE_LIMIT
- AC-006.4: System calculates pro-rata premium adjustment
- AC-006.5: System generates Endorsement Number (END-YYYY-NNNNNN)
- AC-006.6: Endorsement status: DRAFT → PENDING_APPROVAL → APPROVED → EFFECTIVE
- AC-006.7: Premium adjustment applied after endorsement approval
- AC-006.8: Endorsement creates audit trail entry

**Error Scenarios:**
- E-006.1: Policy not ACTIVE → 422 "Endorsement only allowed on active policies"
- E-006.2: Endorsement effective date outside policy period → 422 "Endorsement effective date out of policy period"
- E-006.3: Resulting aggregate limit exceeds maximum → 422 "Coverage would exceed policy aggregate limit"
- E-006.4: Insufficient premium collected → 402 "Payment required for endorsement"

---

#### US-007: Policy Renewal
**As a** Underwriter or System
**I want to** generate renewal quotes for expiring policies
**So that** Policyholders can renew without lapse in coverage
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-007.1: System identifies policies within 60 days of expiration
- AC-007.2: Renewal quote automatically generated with new premiums
- AC-007.3: Renewal quote preserves existing Coverage structure
- AC-007.4: Premium recalculated with current rating factors
- AC-007.5: Renewal quote must be binding by expiration date
- AC-007.6: Renewal notice sent to Policyholder 30 days before expiration
- AC-007.7: If not renewed by expiration, policy status → EXPIRED
- AC-007.8: Renewal creates audit trail entry

**Error Scenarios:**
- E-007.1: Policyholder ineligible for renewal → 422 "Policyholder ineligible for renewal"
- E-007.2: Rating engine fails → 500 with manual underwriting workflow initiated
- E-007.3: Premium calculation error → 500 "Unable to calculate renewal premium"

---

#### US-008: Policy Cancellation
**As a** Policyholder or Agent
**I want to** cancel an active policy
**So that** I can end coverage
**Priority:** Medium | **Story Points:** 5

**Acceptance Criteria:**
- AC-008.1: Cancellation allowed on ACTIVE or ISSUED policies
- AC-008.2: Cancellation Reason captured (customer request, non-payment, replacement)
- AC-008.3: Cancellation Notice generated with 30-day notice period
- AC-008.4: Policy status transitions: ACTIVE → CANCELLATION_PENDING → CANCELLED
- AC-008.5: Pro-rata refund calculated based on days remaining
- AC-008.6: Refund processed within 10 business days
- AC-008.7: Cancellation creates audit trail with reason and timestamp

**Error Scenarios:**
- E-008.1: Policy not ACTIVE → 422 "Cannot cancel non-active policy"
- E-008.2: Outstanding claims prevent cancellation → 422 "Outstanding claims must be resolved"
- E-008.3: Refund processing fails → 500 "Unable to process refund"

---

### Claims Management

#### US-009: Claim Filing (First Notice of Loss - FNOL)
**As a** Policyholder or Claims Representative
**I want to** file a claim (FNOL) to initiate the claims process
**So that** a covered loss can be investigated and settled
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-009.1: User enters Policy Number or Insured Name to locate policy
- AC-009.2: System verifies Policy is ACTIVE on Date of Loss
- AC-009.3: User selects claimed Coverage Type
- AC-009.4: System verifies Coverage Type exists on Policy
- AC-009.5: User enters Date of Loss, Loss Type (COLLISION, THEFT, FIRE, WATER, LIABILITY, etc.)
- AC-009.6: User enters Loss Description and estimated loss amount
- AC-009.7: System assigns Claim Number (CLM-YYYY-NNNNNN)
- AC-009.8: System sets initial Reserve Amount = estimated loss amount (capped at Coverage Limit)
- AC-009.9: Claim status set to FNOL
- AC-009.10: Claimant contact information captured (name, phone, email, address)
- AC-009.11: FNOL creates audit trail entry

**Error Scenarios:**
- E-009.1: Policy not active on Date of Loss → 400 "Policy was not active on date of loss"
- E-009.2: Coverage Type not found on Policy → 400 "Coverage type not found on policy"
- E-009.3: Date of Loss outside policy period → 422 "Date of loss outside policy effective/expiration dates"
- E-009.4: Claimed amount exceeds Coverage Limit → 200 (warning) "Claimed amount exceeds coverage limit"
- E-009.5: Policy expired more than 90 days ago → 422 "Cannot file claim on expired policy"

---

#### US-010: Claim Search and History
**As a** Claims Adjuster or Policyholder
**I want to** search for and view claim history
**So that** I can track and manage claims
**Priority:** High | **Story Points:** 5

**Acceptance Criteria:**
- AC-010.1: Search supports Claim Number, Policy Number, Insured Name
- AC-010.2: Search supports Claim Status (FNOL, UNDER_REVIEW, APPROVED, DENIED, SETTLED, CLOSED, REOPENED)
- AC-010.3: Search supports Date of Loss range
- AC-010.4: Results returned within 3 seconds
- AC-010.5: Claim History displays: Claim Number, Date of Loss, Claim Status, Loss Type, Reserve Amount, Paid Amount
- AC-010.6: Sorted by Date of Loss (most recent first)
- AC-010.7: Filterable by Claim Status
- AC-010.8: "No prior claims exist for this policy" message if none found

**Error Scenarios:**
- E-010.1: No matching claims found → 200 "No matching claims found"
- E-010.2: Unauthorized access attempt → 403 "Insufficient permissions"
- E-010.3: Search timeout → 504 "Search request timed out"

---

#### US-011: Claim Investigation and Adjustment
**As a** Claims Adjuster
**I want to** investigate a claim and determine the payout amount
**So that** the claim can be settled or denied
**Priority:** High | **Story Points:** 13

**Acceptance Criteria:**
- AC-011.1: Adjuster reviews FNOL claim details
- AC-011.2: Adjuster can add investigation notes and attach supporting documents
- AC-011.3: Adjuster verifies Claimant identity and contact information
- AC-011.4: Adjuster reviews Coverage Type and Deductible applicability
- AC-011.5: Adjuster requests additional information if needed
- AC-011.6: Claim status transitions: FNOL → UNDER_REVIEW → APPROVED/DENIED
- AC-011.7: Adjuster determines Reserve Adjustment Amount based on investigation
- AC-011.8: System calculates Settlement Amount = Reserve Amount - Deductible
- AC-011.9: For denied claims, denial reason code must be specified (COVERAGE_NOT_APPLICABLE, EXCLUSION_APPLIES, FRAUD_SUSPECTED, etc.)
- AC-011.10: Investigation creates audit trail with adjuster ID and timestamp

**Error Scenarios:**
- E-011.1: Claim not in FNOL or UNDER_REVIEW status → 422 "Claim not ready for investigation"
- E-011.2: Coverage Deductible retrieval fails → 500 "Unable to retrieve deductible information"
- E-011.3: Adjuster lacks approval authority → 403 "Insufficient permissions"

---

#### US-012: Claim Settlement / Denial
**As a** Claims Adjuster or Claims Manager
**I want to** settle or deny a claim
**So that** the claim is finalized
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-012.1: Adjuster selects APPROVED claim
- AC-012.2: For Settlement: Settlement Amount set (cannot exceed Coverage Limit - Deductible)
- AC-012.3: System creates payment record linked to Claim
- AC-012.4: Claim status: UNDER_REVIEW → SETTLED or DENIED
- AC-012.5: For Denial: Denial Reason Code and Explanation recorded
- AC-012.6: Payment or denial notice generated and sent to Claimant
- AC-012.7: Settlement creates audit trail entry
- AC-012.8: Reserve amount adjusted to reflect settlement

**Error Scenarios:**
- E-012.1: Claim not in APPROVED status → 422 "Only approved claims can be settled"
- E-012.2: Settlement amount exceeds coverage → 422 "Settlement amount exceeds coverage limit"
- E-012.3: Payment creation fails → 500 "Unable to create payment"
- E-012.4: Notice generation fails → 500 "Unable to generate settlement notice"

---

#### US-013: Claim Reopening
**As a** Claims Adjuster or Litigation Manager
**I want to** reopen a closed claim if new information emerges
**So that** the claim can be re-evaluated
**Priority:** Medium | **Story Points:** 5

**Acceptance Criteria:**
- AC-013.1: Claim must be in CLOSED, SETTLED, or DENIED status
- AC-013.2: Reopening reason must be documented
- AC-013.3: Claim status transitions: [CLOSED/SETTLED/DENIED] → REOPENED
- AC-013.4: Reserve amount can be adjusted
- AC-013.5: Reopening creates audit trail entry
- AC-013.6: Litigation case reference optional

**Error Scenarios:**
- E-013.1: Claim not in closeable status → 422 "Claim not eligible for reopening"
- E-013.2: Reopening reason not provided → 400 "Reopening reason required"

---

#### US-014: Claim-Level Policy Data Management
**As a** Claims Adjuster
**I want to** add or modify policy information at the claim level for unverified policies
**So that** I can process claims even when policy information is incomplete
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-014.1: When claim references unverified or missing policy data, adjuster can edit at claim level
- AC-014.2: Claim-level policy data is stored separately from original Policy record
- AC-014.3: Visual indicator (flag, icon) shows when claim uses claim-level policy data
- AC-014.4: All changes to claim-level policy data logged to audit trail (user, timestamp, before/after values)
- AC-014.5: Original Policy record is never overwritten by claim-level changes
- AC-014.6: Claim-level data fields: Coverage Type, Limit, Deductible, Location, Vehicle Details (if AUTO)
- AC-014.7: Claim processor notified when claim-level data differs from policy data

**Error Scenarios:**
- E-014.1: Claim-level policy data cannot be saved → 500 "Unable to save claim-level policy data. Please try again later."
- E-014.2: User lacks edit permission → 403 "Insufficient permissions"

---

#### US-015: Subrogation and Recovery Tracking
**As a** Recovery Manager
**I want to** track subrogation and third-party recovery opportunities
**So that** we can recover losses from responsible parties
**Priority:** Medium | **Story Points:** 8

**Acceptance Criteria:**
- AC-015.1: Claim can be linked to Subrogation Case
- AC-015.2: Subrogation status tracked: IDENTIFIED, REFERRED, PENDING, SETTLED, CLOSED
- AC-015.3: Recoverable amount calculated based on Paid Claim Amount
- AC-015.4: Third-party information captured (name, insurance company, claim number)
- AC-015.5: Recovery transactions recorded and applied to claim reserve
- AC-015.6: Subrogation linked claims and payments tracked
- AC-015.7: Subrogation creates audit trail entry

**Error Scenarios:**
- E-015.1: Claim not settled → 422 "Subrogation only available for settled claims"
- E-015.2: Invalid third-party information → 400 "Invalid third-party details"

---

#### US-016: Scheduled Payments Management
**As a** Claims Adjuster or Settlement Manager
**I want to** manage scheduled payments (structured settlements, periodic payments)
**So that** we can distribute claim settlements over time
**Priority:** Medium | **Story Points:** 8

**Acceptance Criteria:**
- AC-016.1: Scheduled Payment created for SETTLED claims
- AC-016.2: Payment Schedule Type supported: STRUCTURED_SETTLEMENT, PERIODIC_LUMP_SUM, STRUCTURED_BUYOUT
- AC-016.3: Payment Schedule specifies: Total Amount, Payment Frequency (monthly, quarterly, annual), Duration, Current Due Date, Balance Remaining
- AC-016.4: Payee information captured: Recipient Name, Address, Payment Method
- AC-016.5: Payment Schedule status: ACTIVE, SUSPENDED, COMPLETED
- AC-016.6: Individual payments tracked within schedule (amount, date, status)
- AC-016.7: Scheduled Payment creates audit trail entry

**Error Scenarios:**
- E-016.1: Claim not SETTLED → 422 "Scheduled payments only for settled claims"
- E-016.2: Invalid payment schedule → 400 "Invalid payment schedule parameters"

---

### Payments & Disbursements

#### US-017: Payment Method Configuration
**As an** Admin or Finance Manager
**I want to** configure supported payment methods for disbursements
**So that** we can process payments via multiple channels
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-017.1: Supported payment methods: ACH, Wire Transfer, Credit/Debit Card, Stripe Connect, Global Payouts
- AC-017.2: Each payment method has enabled/disabled status
- AC-017.3: Each payment method configured with: Processor details, API credentials (encrypted), fee structure, daily/monthly limits
- AC-017.4: Payment routing rules defined: default method by payee type, exception handling
- AC-017.5: KYC/Identity verification requirements configured per method
- AC-017.6: Compliance settings (tax reporting, withholding rules)
- AC-017.7: Configuration changes logged to audit trail

**Error Scenarios:**
- E-017.1: Invalid payment method → 400 "Invalid payment method"
- E-017.2: Credential encryption fails → 500 "Unable to save payment credentials"
- E-017.3: User lacks configuration permission → 403 "Insufficient permissions"

---

#### US-018: Payee (Vendor/Claimant) Onboarding
**As a** Finance Manager or Claims Processor
**I want to** onboard vendors and claimants with payment method verification
**So that** payments can be processed securely
**Priority:** High | **Story Points:** 13

**Acceptance Criteria:**
- AC-018.1: Payee profile creation: Type (VENDOR, CLAIMANT, PROVIDER)
- AC-018.2: Payee information collected: Legal Name, Tax ID (SSN/EIN), Address, Contact (phone, email)
- AC-018.3: KYC (Know Your Customer) verification required: Identity verification (government ID), address verification, beneficial owner info if applicable
- AC-018.4: Bank account verification: Routing number, account number (masked for display), account holder name, account type (checking/savings)
- AC-018.5: Payee status: PENDING_VERIFICATION, VERIFIED, BLOCKED, INACTIVE
- AC-018.6: Payee can have multiple payment methods on file
- AC-018.7: Tax identification and 1099 reporting flags configured
- AC-018.8: Onboarding creates audit trail entry

**Error Scenarios:**
- E-018.1: KYC verification fails → 422 "KYC verification failed for payee"
- E-018.2: Bank account verification fails → 422 "Bank account verification failed"
- E-018.3: Duplicate payee detected → 409 "Payee already exists"
- E-018.4: Required information missing → 400 "Missing required payee information"

---

#### US-019: Payment Creation
**As a** Claims Adjuster or Finance Manager
**I want to** create a payment record linked to a claim or policy
**So that** a settlement or reimbursement can be disbursed
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-019.1: Payment linked to Claim Number or Policy Number
- AC-019.2: Payee selected from verified Payee list
- AC-019.3: Payment Method selected (ACH, Wire, Card, Stripe, Global Payouts)
- AC-019.4: Payment Amount entered (positive, negative, or zero allowed per business logic)
- AC-019.5: Deductions captured: Applicable Taxes (income tax withholding), Medical/Legal Fees, Court Costs
- AC-019.6: Net Payment Amount calculated: Amount - Deductions + (if negative payment) reversals
- AC-019.7: Payment Type specified: SETTLEMENT, REIMBURSEMENT, DISBURSEMENT, REVERSAL, REISSUE, VOID
- AC-019.8: Eroding vs. Non-Eroding Reserve designation: ERODING (reduces reserve) or NON_ERODING
- AC-019.9: Reserve Line allocation: Payment allocated to one or more reserve lines
- AC-019.10: Joint Payee support: Multiple payees with payment portions defined
- AC-019.11: Payment status: DRAFT, PENDING_APPROVAL, APPROVED, PROCESSING, PROCESSED, CANCELLED, FAILED
- AC-019.12: Payment creates audit trail entry

**Error Scenarios:**
- E-019.1: Payee not verified → 422 "Payee not verified"
- E-019.2: Payment amount exceeds claim settlement → 422 "Payment amount exceeds claim settlement"
- E-019.3: Claim not SETTLED → 422 "Payment only allowed for settled claims"
- E-019.4: Invalid deduction combination → 400 "Invalid deductions"

---

#### US-020: Payment Approval Workflow
**As a** Finance Manager or Payment Approver
**I want to** review and approve pending payments
**So that** only authorized payments are processed
**Priority:** High | **Story Points:** 5

**Acceptance Criteria:**
- AC-020.1: Payment approval required based on amount threshold (e.g., > $5,000)
- AC-020.2: Approver can view payment details: amount, payee, claim, reserve allocation
- AC-020.3: Approver can approve or reject payment with reason
- AC-020.4: On approval, payment status: PENDING_APPROVAL → APPROVED → PROCESSING
- AC-020.5: On rejection, payment status: PENDING_APPROVAL → REJECTED (with reason logged)
- AC-020.6: Approval creates audit trail entry
- AC-020.7: Automated emails sent on approval/rejection

**Error Scenarios:**
- E-020.1: Approver lacks permission → 403 "Insufficient permissions"
- E-020.2: Payment not in PENDING_APPROVAL status → 422 "Payment not pending approval"
- E-020.3: Rejection reason not provided → 400 "Rejection reason required"

---

#### US-021: Payment Processing and Disbursement
**As a** Finance System
**I want to** process approved payments via configured payment methods
**So that** funds are transferred to payees
**Priority:** High | **Story Points:** 13

**Acceptance Criteria:**
- AC-021.1: Payment processing triggered after approval (manual or automatic)
- AC-021.2: Payment method validation: payee verified, routing rules applied
- AC-021.3: ACH transactions: Create ACH file with routing number, account number, amount, originating bank info
- AC-021.4: Wire transfers: Create wire instruction with banking details, SWIFT/IBAN if international
- AC-021.5: Credit/Debit Card: Process via card processor (Stripe, etc.)
- AC-021.6: Stripe Connect: Create transfer to connected Stripe account
- AC-021.7: Global Payouts: Route via global payout service with currency conversion if needed
- AC-021.8: Payment status: APPROVED → PROCESSING → PROCESSED (or FAILED)
- AC-021.9: Confirmation number/reference generated (ACH trace number, wire reference, card auth code)
- AC-021.10: Payment processing creates audit trail entry
- AC-021.11: Reserve amount adjusted based on eroding/non-eroding flag
- AC-021.12: Claimant/Payee notification sent

**Error Scenarios:**
- E-021.1: Payment method processing fails → 500 "Unable to process payment via selected method"
- E-021.2: Insufficient funds in account → 402 "Insufficient funds"
- E-021.3: ACH/Wire validation fails → 400 "Invalid banking details"
- E-021.4: Processor decline → 402 "Payment declined by processor"
- E-021.5: Network timeout → 504 "Payment processor timeout"

---

#### US-022: Payment Reversal, Void, and Reissue
**As a** Finance Manager or Claims Adjuster
**I want to** reverse, void, or reissue payments if needed
**So that** erroneous payments can be corrected
**Priority:** Medium | **Story Points:** 8

**Acceptance Criteria:**
- AC-022.1: VOID: Cancel DRAFT or PENDING_APPROVAL payment (no funds transferred)
- AC-022.2: REVERSAL: Reverse PROCESSED payment (refund to payee's original account)
- AC-022.3: REISSUE: Reprocess a failed payment or issue replacement payment
- AC-022.4: Each action requires reason code (INCORRECT_AMOUNT, DUPLICATE, WRONG_PAYEE, etc.)
- AC-022.5: Void/Reversal generates credit memo linked to original payment
- AC-022.6: Reserve restored if eroding payment is reversed
- AC-022.7: Reversal creates new payment record with REVERSAL type
- AC-022.8: All actions logged to audit trail

**Error Scenarios:**
- E-022.1: Payment not in eligible status → 422 "Payment cannot be reversed in current status"
- E-022.2: Reversal processing fails → 500 "Unable to process reversal"
- E-022.3: User lacks reversal permission → 403 "Insufficient permissions"

---

#### US-023: Tax Withholding and 1099 Reporting
**As a** Finance Manager
**I want to** withhold taxes on payments and track 1099 reportable amounts
**So that** we comply with tax regulations
**Priority:** Medium | **Story Points:** 8

**Acceptance Criteria:**
- AC-023.1: Income tax withholding applied per payee configuration (percentage or amount)
- AC-023.2: Withholding amount deducted from payment and held in suspense account
- AC-023.3: 1099 Flag set on payments for VENDOR and INDEPENDENT_CONTRACTOR payee types
- AC-023.4: Tax ID (SSN/EIN) captured and stored (encrypted) for 1099 reporting
- AC-023.5: Annual 1099 report generated: Payee, Tax ID, Total 1099 Reportable Payments
- AC-023.6: Withholding creates audit trail entry

**Error Scenarios:**
- E-023.1: Tax withholding calculation fails → 500 "Unable to calculate withholding"
- E-023.2: Tax ID missing for 1099 payee → 400 "Tax ID required for 1099 reporting"

---

#### US-024: Reserve and Payment Allocation
**As a** Claims Adjuster
**I want to** allocate payments across multiple reserve lines
**So that** complex claims with multiple damages types can be properly accounted for
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-024.1: Claim can have multiple reserve lines: Medical Reserve, Property Damage Reserve, Liability Reserve, Subrogation Reserve, etc.
- AC-024.2: Payment can be allocated to one or more reserve lines
- AC-024.3: Payment allocation shows: Reserve Line, Amount Allocated, Percentage of Payment
- AC-024.4: Total allocated amount = payment amount (validation)
- AC-024.5: Reserve balance tracked after payment: Previous Balance - Allocated Amount = New Balance
- AC-024.6: Allocation supports eroding (reduces limit) and non-eroding allocations
- AC-024.7: Allocation creates audit trail entry

**Error Scenarios:**
- E-024.1: Allocation total doesn't equal payment amount → 400 "Allocation total must equal payment amount"
- E-024.2: Reserve line not found → 404 "Reserve line not found"
- E-024.3: Insufficient reserve balance → 422 "Insufficient reserve balance for allocation"

---

#### US-025: Joint Payee Payment Management
**As a** Claims Adjuster
**I want to** split payments between multiple joint payees
**So that** repairs/settlements can be paid to multiple parties (e.g., policyholder and repair shop)
**Priority:** Medium | **Story Points:** 8

**Acceptance Criteria:**
- AC-025.1: Payment can have multiple payees (joint payees)
- AC-025.2: Payment portion defined for each payee (amount or percentage)
- AC-025.3: Payment portions add up to total payment amount (validation)
- AC-025.4: Each payee can have different payment methods
- AC-025.5: Individual payment transactions created for each payee
- AC-025.6: All payees must be verified before payment processing
- AC-025.7: Joint payee setup creates audit trail entry

**Error Scenarios:**
- E-025.1: Payee portions don't sum to total → 400 "Payee portions must sum to payment amount"
- E-025.2: Unverified payee in joint payment → 422 "All joint payees must be verified"

---

#### US-026: External Estimate Integration (Xactimate/XactAnalysis)
**As a** Claims Adjuster
**I want to** import line items from external estimates (Xactimate, XactAnalysis)
**So that** I can create payable items automatically
**Priority:** Medium | **Story Points:** 13

**Acceptance Criteria:**
- AC-026.1: External estimate file uploaded (Xactimate JSON/XML, XactAnalysis format)
- AC-026.2: System parses estimate and extracts line items: Description, Quantity, Unit Price, Total Amount
- AC-026.3: Line items imported as reserve lines or payment line items
- AC-026.4: Adjuster can accept, modify, or reject individual line items
- AC-026.5: Approved line items converted to reserve amounts or payment records
- AC-026.6: Estimate tracking: file name, upload date, parsed line count, accepted count
- AC-026.7: Integration creates audit trail entry

**Error Scenarios:**
- E-026.1: Invalid file format → 400 "Invalid estimate file format"
- E-026.2: Parsing error → 500 "Unable to parse estimate file"
- E-026.3: Estimate total exceeds coverage limit → 422 "Estimate exceeds coverage limit" (warning, not error)

---

#### US-027: Document Attachment to Payments
**As a** Claims Adjuster
**I want to** attach supporting documents to payment records
**So that** payment justification is documented
**Priority:** Medium | **Story Points:** 5

**Acceptance Criteria:**
- AC-027.1: Payment record can have one or more attached documents
- AC-027.2: Supported file types: PDF, image (JPG, PNG), Word (DOCX)
- AC-027.3: Document metadata captured: file name, upload date, file size, uploader name
- AC-027.4: Documents stored in document management system (encrypted)
- AC-027.5: Document attachment creates audit trail entry

**Error Scenarios:**
- E-027.1: Unsupported file type → 400 "Unsupported file type"
- E-027.2: File size exceeds limit (50 MB) → 413 "File size exceeds limit"
- E-027.3: Upload fails → 500 "Unable to upload document"

---

#### US-028: EDI/EOB Remittance to Medical Providers
**As a** Medical Claims Administrator
**I want to** generate EDI 835 remittances and EOB statements for medical providers
**So that** providers receive standardized remittance information
**Priority:** Low | **Story Points:** 13

**Acceptance Criteria:**
- AC-028.1: EDI 835 (Healthcare Payment Advice) generated for medical claim payments
- AC-028.2: EDI format includes: Claim reference, CPT codes, ICD codes, allowed amount, paid amount, adjustments
- AC-028.3: Mapping of claim items to CPT (procedure) and ICD (diagnosis) codes supported
- AC-028.4: Adjustments tracked: contractual adjustment, denial reason, patient responsibility
- AC-028.5: Remittance can be downloaded as EDI 835 file or printed as EOB statement
- AC-028.6: Bill review vendor integration for pre-payment review
- AC-028.7: EDI generation creates audit trail entry

**Error Scenarios:**
- E-028.1: CPT/ICD mapping not found → 422 "CPT/ICD codes not mapped for claim items"
- E-028.2: EDI generation fails → 500 "Unable to generate EDI remittance"

---

#### US-029: Payment Routing Rules Configuration
**As an** Admin
**I want to** configure payment routing rules
**So that** payments are automatically routed to the correct payment method based on business rules
**Priority:** Medium | **Story Points:** 8

**Acceptance Criteria:**
- AC-029.1: Routing rule conditions: Payee Type, Claim Type, Amount Range, Geographic Location
- AC-029.2: Routing rule actions: Default Payment Method, Exception Handler, Approval Threshold
- AC-029.3: Rule priority and execution order defined
- AC-029.4: Rules can be enabled/disabled
- AC-029.5: Sample rules: ACH for vendor payments > $1,000, Wire for settlement > $10,000, Card for < $500
- AC-029.6: Rule testing capability (dry-run)
- AC-029.7: Routing rule creation logged to audit trail

**Error Scenarios:**
- E-029.1: Invalid rule condition → 400 "Invalid routing rule condition"
- E-029.2: Rule conflict detected → 409 "Routing rule conflicts with existing rules"

---

### Integration and System Requirements

#### US-030: Audit Trail and Compliance Logging
**As an** Auditor or Compliance Officer
**I want to** view comprehensive audit logs of all system actions
**So that** we maintain regulatory compliance and accountability
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-030.1: Audit log captures all policy actions: create, update, endorse, renew, cancel
- AC-030.2: Audit log captures all claim actions: FNOL, investigation, adjustment, settlement, denial, reopen
- AC-030.3: Audit log captures all payment actions: creation, approval, processing, reversal, void
- AC-030.4: Each audit entry includes: User ID, User Role, Timestamp, Entity Type, Entity ID, Action, Before Values, After Values, IP Address
- AC-030.5: Audit logs stored in immutable data store
- AC-030.6: Audit logs retained for minimum 7 years per regulatory requirements
- AC-030.7: Audit log search/filter: date range, user, entity type, action, entity ID
- AC-030.8: Sensitive data (SSN, payment info) masked in audit logs

**Error Scenarios:**
- E-030.1: Audit log write fails → 500 "Unable to write audit log"
- E-030.2: Audit query timeout → 504 "Audit log query timed out"

---

#### US-031: Role-Based Access Control (RBAC)
**As an** Admin
**I want to** configure roles and permissions
**So that** users can only access data and perform actions authorized for their role
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-031.1: Role types: Agent, Underwriter, Claims Adjuster, Finance Manager, Recovery Manager, Admin, Auditor
- AC-031.2: Each role has defined permissions: read, create, update, approve, process payments
- AC-031.3: Users assigned to one or more roles
- AC-031.4: Permissions enforced at API and UI level
- AC-031.5: Permission checks include entity-level restrictions (e.g., adjuster can only view assigned claims)
- AC-031.6: Role assignment changes logged to audit trail
- AC-031.7: User account status: ACTIVE, INACTIVE, LOCKED

**Error Scenarios:**
- E-031.1: User lacks required permission → 403 "Insufficient permissions"
- E-031.2: User role not found → 404 "User role not found"

---

#### US-032: Data Encryption and PII Protection
**As a** Security Officer
**I want to** ensure all sensitive data is encrypted and PII is protected
**So that** we comply with data protection regulations
**Priority:** High | **Story Points:** 13

**Acceptance Criteria:**
- AC-032.1: At-rest encryption: SSN, TIN, payment information, bank account numbers encrypted in database
- AC-032.2: In-transit encryption: All API traffic uses HTTPS with TLS 1.2+
- AC-032.3: Encryption keys managed via key management service (KMS) with rotation policy
- AC-032.4: PII masking in UI: SSN display format: XXX-XX-1234, account display: ...7890
- AC-032.5: Sensitive data never logged in plain text (masked in logs)
- AC-032.6: Backup encryption: Database backups encrypted at rest
- AC-032.7: Encryption implementation reviewed annually

**Error Scenarios:**
- E-032.1: Encryption key unavailable → 500 "Encryption service unavailable"
- E-032.2: Decryption failure → 500 "Data decryption failed"

---

#### US-033: Payment Gateway Integration
**As a** Finance System
**I want to** integrate with external payment processors
**So that** we can process payments via multiple channels
**Priority:** High | **Story Points:** 13

**Acceptance Criteria:**
- AC-033.1: Stripe Connect integration: OAuth authentication, account linking, payout management
- AC-033.2: Global Payouts integration: Multi-currency support, country routing, compliance checks
- AC-033.3: ACH provider integration: Batch file creation, submission, reconciliation
- AC-033.4: Wire transfer integration: Banking partner API, instruction validation, confirmation
- AC-033.5: Processor API error handling: Retry logic (exponential backoff), circuit breaker pattern
- AC-033.6: Payment status synchronization: Periodic polling or webhook-based updates
- AC-033.7: Processor fee tracking: fees captured and reconciled monthly
- AC-033.8: Integration testing with sandbox environments before production deployment

**Error Scenarios:**
- E-033.1: Processor API error → 500 with retry logic initiated
- E-033.2: Authentication failure → 401 "Payment processor authentication failed"
- E-033.3: Rate limit exceeded → 429 "Payment processor rate limit exceeded"

---

#### US-034: Bank Account and ACH/Wire Processing
**As a** Finance Manager
**I want to** manage company bank accounts and process ACH/Wire transfers
**So that** we can disburse payments to payees
**Priority:** High | **Story Points:** 8

**Acceptance Criteria:**
- AC-034.1: Bank account configuration: Routing number, account number (encrypted), account type, account name
- AC-034.2: ACH file format: NACHA standard ACH file generation
- AC-034.3: ACH batch setup: Batch ID, company identification, origination date, settlement date
- AC-034.4: Wire transfer details: Beneficiary bank, beneficiary account, amount, purpose
- AC-034.5: SWIFT/IBAN support for international transfers
- AC-034.6: Micro-deposit verification for new ACH accounts (optional)
- AC-034.7: Daily transaction limits enforced per bank policy
- AC-034.8: Account setup creates audit trail entry

**Error Scenarios:**
- E-034.1: Invalid routing number → 400 "Invalid routing number format"
- E-034.2: Account verification fails → 422 "Bank account verification failed"
- E-034.3: Daily transaction limit exceeded → 429 "Daily transaction limit exceeded"

---

#### US-035: System Integration with External Data Sources
**As a** Claims Processor
**I want to** fetch and integrate data from external systems
**So that** claims processing is streamlined and data is current
**Priority:** Medium | **Story Points:** 8

**Acceptance Criteria:**
- AC-035.1: Litigation Data integration: Case information, attorney details, trial dates
- AC-035.2: Tax ID lookup: Validate payee Tax ID via IRS/SSA services
- AC-035.3: Accounting System integration: Cost tracking, journal entry creation, reconciliation
- AC-035.4: Agency Markets integration: Agency data, marketplace policies, commissions
- AC-035.5: Document Management integration: Document upload, retrieval, storage
- AC-035.6: Each integration supports error handling and retry logic
- AC-035.7: Integration creates audit trail entries

**Error Scenarios:**
- E-035.1: External system unavailable → 503 "External service unavailable"
- E-035.2: Data mapping error → 500 "Unable to integrate external data"

---

#### US-036: Regulatory Compliance Reporting
**As a** Compliance Officer
**I want to** generate regulatory reports
**So that** we comply with insurance regulatory requirements
**Priority:** Medium | **Story Points:** 8

**Acceptance Criteria:**
- AC-036.1: Annual premium report: Total premiums by policy type and state
- AC-036.2: Claims report: Total claims by type, paid amount, denied amount, average settlement time
- AC-036.3: Loss ratio report: (Total Paid Claims / Total Premiums) by policy type
- AC-036.4: Cancellation report: Reason codes, refunds issued, 30-day notice compliance
- AC-036.5: Data retention verification: Confirm all required records retained 7+ years
- AC-036.6: Reports generated in PDF format with export to Excel
- AC-036.7: Report generation creates audit trail entry

**Error Scenarios:**
- E-036.1: Report generation fails → 500 "Unable to generate report"
- E-036.2: Data not available for period → 400 "Data not available for selected period"

---

## 3. Business Rules

### Policy Rules (POL)
- **POL-001:** Policy number format: POL-YYYY-NNNNNN (auto-generated, sequential)
- **POL-002:** Policy effective date must be today or a future date (not retroactive)
- **POL-003:** Policy expiration date must be after effective date
- **POL-004:** Policy term: 6 months or 12 months
- **POL-005:** Cancellation requires 30-day written notice to comply with regulatory requirements
- **POL-006:** Pro-rata refund calculated: (Days Remaining / Days in Term) × Total Premium
- **POL-007:** Policy cannot be cancelled if active claims exist (must be resolved first)
- **POL-008:** Policy transitions to EXPIRED automatically on expiration date if not renewed

### Coverage Rules (COV)
- **COV-001:** Each Coverage has a Limit (positive decimal value)
- **COV-002:** Deductible must be less than or equal to Limit
- **COV-003:** Sum of all Coverage Limits cannot exceed Policy Aggregate Limit
- **COV-004:** At least one Coverage required per Policy
- **COV-005:** Coverage removed from Policy during Endorsement only if no pending claims exist on that coverage
- **COV-006:** Coverage Limit can be modified via Endorsement with pro-rata premium adjustment

### Premium Rules (PRM)
- **PRM-001:** Premium calculation formula: **Base Rate × Territory Factor × Age Factor × Claims Factor - Discounts + Surcharges**
- **PRM-002:** Base Rate determined by Policy Type and Coverage Type
- **PRM-003:** Territory Factor varies by state/zip code (1.0 - 2.0)
- **PRM-004:** Age Factor varies by Insured age (applies to LIFE, HEALTH policies)
- **PRM-005:** Claims Factor: 1.0 (no prior claims), 1.15 (1 claim in 3 years), 1.30 (2+ claims in 3 years)
- **PRM-006:** Multi-policy discount: 10% if Insured has 2+ active policies
- **PRM-007:** Claims-free discount: 5% for 3+ years without claims
- **PRM-008:** Home security discount: 5% for verified security system
- **PRM-009:** Minimum premium: $100 per policy term
- **PRM-010:** Renewal premium recalculated using current rating factors

### Claim Rules (CLM)
- **CLM-001:** Claim number format: CLM-YYYY-NNNNNN (auto-generated, sequential)
- **CLM-002:** Date of Loss must fall within Policy effective and expiration dates
- **CLM-003:** Claim cannot be filed on expired policy if policy expired > 90 days ago
- **CLM-004:** Claimed amount cannot exceed Coverage Limit for claimed Coverage Type
- **CLM-005:** Deductible applies to each claim (reduces payout)
- **CLM-006:** Reserve amount = min(claimed amount, coverage limit) - deductible
- **CLM-007:** Settlement amount cannot exceed Reserve amount (unless management override)
- **CLM-008:** Denied claims must have reason code: COVERAGE_NOT_APPLICABLE, EXCLUSION_APPLIES, FRAUD_SUSPECTED, etc.
- **CLM-009:** Once claim is SETTLED or DENIED, no further payments without REOPENING claim
- **CLM-010:** Reopened claim must have documented reason (new evidence, litigation development, etc.)

### Payment Rules (PAY)
- **PAY-001:** Payment linked to Claim or Policy
- **PAY-002:** Payee must be VERIFIED status before payment can be PROCESSED
- **PAY-003:** Payment amount cannot exceed: Claim Settlement Amount or Policy Credit Balance
- **PAY-004:** Deduction types: Income tax withholding (percentage per payee config), medical/legal fees, court costs
- **PAY-005:** Eroding payments reduce Reserve Balance; non-eroding payments do not affect reserve
- **PAY-006:** Payment can be allocated to multiple Reserve Lines (sum of allocations = payment amount)
- **PAY-007:** Joint payees: Payment portions sum to total payment amount
- **PAY-008:** ACH transactions limited to US bank accounts (routing number 9 digits)
- **PAY-009:** Wire transfers support international accounts (SWIFT/IBAN)
- **PAY-010:** Payment reversal: Funds returned to payee's original account within 3-5 business days

### Audit Rules (AUD)
- **AUD-001:** All policy actions logged: create, update, endorse, renew, cancel (user, timestamp, before/after values)
- **AUD-002:** All claim actions logged: FNOL, investigation, adjustment, settlement, denial, reopen
- **AUD-003:** All payment actions logged: creation, approval, processing, reversal, void, withholding
- **AUD-004:** Sensitive data (SSN, account numbers) masked in audit logs
- **AUD-005:** Audit logs retained minimum 7 years
- **AUD-006:** Claim-level policy data changes tracked separately: flag indicates claim-level data in use
- **AUD-007:** RBAC changes logged: role assignment, permission grant/revoke

### Regulatory Rules (REG)
- **REG-001:** 30-day cancellation notice required before policy cancellation effective
- **REG-002:** SSN/TIN masked in UI display: XXX-XX-1234 format
- **REG-003:** PCI-DSS compliance required for payment processing (encryption, access control)
- **REG-004:** WCAG AA compliance required for UI (accessibility)
- **REG-005:** 1099 reporting for vendor/independent contractor payments
- **REG-006:** Tax ID validation required for 1099 payees
- **REG-007:** KYC (Know Your Customer) verification required for all payees before first payment
- **REG-008:** Annual compliance audit required (data retention, access controls, encryption)

---

## 4. Policy Lifecycle State Machine

```
Quote
  ↓
Bind (Effective Date Set)
  ↓
Issued (Documents Generated)
  ↓
Active (Coverage Active)
  ├── Endorse (Mid-Term Change)
  │   └── Active (Endorsed Coverage Active)
  ├── Renew (Generate Renewal Quote)
  │   └── Quote (Renewal Quote)
  │       └── Bind (Renewal Binding)
  │           └── Active (Renewed)
  ├── Cancel (Cancellation Notice)
  │   └── Cancelled (Pro-rata Refund Processed)
  └── Expired (Expiration Date Reached)
```

**State Transitions:**
- QUOTED → BOUND: Effective date accepted, premium payment collected
- BOUND → ISSUED: Underwriter approves, documents generated
- ISSUED → ACTIVE: Effective date arrives
- ACTIVE → ACTIVE (Endorse): Modify coverages mid-term
- ACTIVE → EXPIRED: Expiration date arrives without renewal
- ACTIVE → CANCELLED: 30-day cancellation notice + refund processing
- EXPIRED → RENEWED: Renewal quote bound and issued

---

## 5. Claim Lifecycle State Machine

```
FNOL (First Notice of Loss)
  ↓
Under Investigation
  ├── Adjust (Determine Payout)
  │   ├── Approved (Ready for Settlement)
  │   │   ├── Settled (Payment Processed)
  │   │   │   ├── Closed (Final Disposition)
  │   │   │   └── Reopened (New Evidence)
  │   │   │       └── Under Investigation
  │   │   └── Denied (Payment Declined)
  │   │       ├── Closed (Final Disposition)
  │   │       └── Reopened (Appeal)
  │   │           └── Under Investigation
  │   └── Denied (Coverage Not Applicable)
  │       └── Closed
  └── Request Additional Info
      └── Under Investigation
```

**State Transitions:**
- FNOL → UNDER_REVIEW: Initial investigation begins
- UNDER_REVIEW → APPROVED: Coverage verified, reserve estimated
- UNDER_REVIEW → DENIED: Coverage not applicable or exclusion applies
- APPROVED → SETTLED: Claimant agrees to settlement amount
- APPROVED → DENIED: Additional investigation reveals exclusion
- SETTLED → CLOSED: Payment processed, claim finalized
- DENIED → CLOSED: Denial final, no appeal
- SETTLED/DENIED/CLOSED → REOPENED: New evidence or appeal filed

---

## 6. Non-Functional Requirements

### Performance
- **NFR-001:** Policy search results returned within 3 seconds (< 100 results)
- **NFR-002:** Policy detail view loaded within 5 seconds
- **NFR-003:** Claim history retrieved within 5 seconds
- **NFR-004:** Premium calculation completed within 2 seconds
- **NFR-005:** Payment processing initiated within 5 seconds (ACH/Wire submission)
- **NFR-006:** API CRUD operations: < 500ms response time
- **NFR-007:** Complex calculations (premium, reserve): < 2 seconds
- **NFR-008:** Support concurrent user sessions (1000+) without degradation

### Availability & Reliability
- **NFR-009:** System availability: 99.9% uptime (monthly)
- **NFR-010:** Payment transaction integrity: No lost or duplicate payments
- **NFR-011:** Payment APIs must be idempotent (safe to retry without side effects)
- **NFR-012:** Database transaction consistency: ACID properties enforced
- **NFR-013:** Automatic failover for critical services (payment processor, database)

### Scalability
- **NFR-014:** Horizontal scaling: Application servers can be added without restart
- **NFR-015:** Database scaling: Read replicas for reporting, write master for transactions
- **NFR-016:** API rate limiting: Per-user (1000 req/min), per-endpoint (10k req/min)

### Security
- **NFR-017:** All API traffic encrypted via HTTPS/TLS 1.2+
- **NFR-018:** PII data encrypted at rest (AES-256)
- **NFR-019:** Payment card data NOT stored (PCI-DSS scope excluded via tokenization)
- **NFR-020:** Session tokens expire after 30 minutes of inactivity
- **NFR-021:** Failed login attempts locked after 5 attempts (15-minute lockout)
- **NFR-022:** All database connections use encrypted authentication

### Accessibility
- **NFR-023:** UI compliant with WCAG 2.1 Level AA
- **NFR-024:** Keyboard navigation fully supported
- **NFR-025:** Screen reader compatibility verified (NVDA, JAWS)
- **NFR-026:** Color contrast ratio >= 4.5:1 for normal text

### Data Protection & Compliance
- **NFR-027:** Audit logs immutable, retained 7 years minimum
- **NFR-028:** PII masking in logs: SSN (XXX-XX-####), account (****7890)
- **NFR-029:** Data retention: Policy records kept 7 years post-expiration
- **NFR-030:** GDPR compliance: Right to deletion (for personal data), data portability
- **NFR-031:** Annual compliance audit: Security controls, encryption, access logs

### Integration & Reliability
- **NFR-032:** External service integration error handling: Exponential backoff retry (3 attempts)
- **NFR-033:** Circuit breaker pattern: Fail fast if external service unavailable
- **NFR-034:** Webhook timeout: 30 seconds, automatic retry up to 5 times
- **NFR-035:** Payment processor redundancy: Primary + backup processor configured

---

## 7. ACORD Domain Model

### Insured (Party)
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| insured_id | Long | PK | Unique identifier |
| type | Enum | INDIVIDUAL, ORGANIZATION | Insured type |
| first_name | String(100) | Required (INDIVIDUAL) | Individual first name |
| last_name | String(100) | Required (INDIVIDUAL) | Individual last name |
| date_of_birth | Date | Required (INDIVIDUAL) | DOB for eligibility/rating |
| organization_name | String(200) | Required (ORGANIZATION) | Business legal name |
| ssn_tin | String(11) | Encrypted, masked | SSN (INDIVIDUAL) or EIN (ORGANIZATION) |
| email | String(255) | Unique | Primary email contact |
| phone | String(20) | | Primary phone number |
| address_line1 | String(255) | | Mailing address |
| address_line2 | String(255) | Optional | Apt/Suite |
| city | String(100) | | City |
| state | String(2) | | State code |
| zip_code | String(10) | | ZIP code |
| occupation | String(100) | Optional | Occupation (for rating) |
| created_at | DateTime | Auto | Record creation |
| updated_at | DateTime | Auto | Last update |

### Policy
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| policy_id | Long | PK | Unique identifier |
| policy_number | String | Unique, Format: POL-YYYY-NNNNNN | ACORD policy number |
| insured_id | Long | FK → Insured | Link to Insured |
| policy_type | Enum | AUTO, HOME, LIFE, HEALTH, COMMERCIAL | Coverage type |
| status | Enum | QUOTED, BOUND, ISSUED, ACTIVE, CANCELLED, EXPIRED | Policy status |
| effective_date | Date | >= Today | Coverage start date |
| expiration_date | Date | > effective_date | Coverage end date |
| aggregate_limit | Decimal(12,2) | > 0 | Max payout for all claims |
| total_premium | Decimal(12,2) | >= 100 | Annual premium |
| term_length | Enum | 6_MONTHS, 12_MONTHS | Policy term |
| created_at | DateTime | Auto | Record creation |
| updated_at | DateTime | Auto | Last update |

### Coverage
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| coverage_id | Long | PK | Unique identifier |
| policy_id | Long | FK → Policy | Parent policy |
| coverage_code | String(10) | | ACORD coverage code |
| coverage_type | Enum | LIABILITY, COLLISION, COMPREHENSIVE, MEDICAL, etc. | Coverage type |
| limit_amount | Decimal(12,2) | > 0, <= policy.aggregate_limit | Maximum payout |
| deductible_amount | Decimal(12,2) | >= 0, <= limit_amount | Insured's out-of-pocket |
| premium_portion | Decimal(12,2) | > 0 | Premium for this coverage |
| status | Enum | ACTIVE, INACTIVE, REMOVED | Coverage status |
| created_at | DateTime | Auto | Record creation |

### Premium
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| premium_id | Long | PK | Unique identifier |
| policy_id | Long | FK → Policy | Link to policy |
| base_rate | Decimal(12,2) | > 0 | Base premium amount |
| territory_factor | Decimal(4,2) | 1.0 - 2.0 | Territory multiplier |
| age_factor | Decimal(4,2) | 0.8 - 1.5 | Age rating factor |
| claims_factor | Decimal(4,2) | 1.0 - 1.5 | Prior claims factor |
| discount_multi_policy | Decimal(12,2) | >= 0 | Multi-policy discount |
| discount_claims_free | Decimal(12,2) | >= 0 | Claims-free discount |
| discount_home_security | Decimal(12,2) | >= 0 | Security discount |
| surcharge_amount | Decimal(12,2) | >= 0 | Surcharges applied |
| total_premium | Decimal(12,2) | >= 100 | Final premium (formula) |
| effective_date | Date | | Premium effective date |
| created_at | DateTime | Auto | Premium calculation date |

### Claim
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| claim_id | Long | PK | Unique identifier |
| claim_number | String | Unique, Format: CLM-YYYY-NNNNNN | ACORD claim number |
| policy_id | Long | FK → Policy | Associated policy |
| status | Enum | FNOL, UNDER_REVIEW, APPROVED, DENIED, SETTLED, CLOSED, REOPENED | Claim status |
| date_of_loss | Date | Within policy period | Loss date |
| reported_date | Date | Auto | FNOL report date |
| loss_type | Enum | COLLISION, THEFT, FIRE, WATER, LIABILITY, etc. | Loss type code |
| loss_description | Text | | Description of loss |
| claimed_coverage_type | Enum | Matches policy coverage | Coverage type claimed |
| claimed_amount | Decimal(12,2) | <= coverage limit | Amount claimed |
| reserve_amount | Decimal(12,2) | Initial estimate | Reserve for potential payout |
| reserve_current | Decimal(12,2) | Adjusted during investigation | Current reserve balance |
| settlement_amount | Decimal(12,2) | <= reserve - deductible | Approved payout |
| paid_amount | Decimal(12,2) | <= settlement | Amount actually paid |
| denial_reason | String(50) | If status = DENIED | Reason code for denial |
| deductible_applied | Decimal(12,2) | >= 0 | Deductible deducted from payout |
| subrogation_applicable | Boolean | | Potential third-party recovery |
| litigation_case_id | String | Optional | Linked litigation case |
| created_at | DateTime | Auto | Claim creation date |
| updated_at | DateTime | Auto | Last update |

### ClaimAdjustment
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| adjustment_id | Long | PK | Unique identifier |
| claim_id | Long | FK → Claim | Associated claim |
| adjustment_type | Enum | RESERVE_INCREASE, RESERVE_DECREASE, SETTLEMENT_APPROVED, SETTLEMENT_DENIED | Adjustment type |
| previous_amount | Decimal(12,2) | | Before value |
| new_amount | Decimal(12,2) | | After value |
| reason | Text | | Reason for adjustment |
| adjusted_by | String | | Adjuster user ID |
| created_at | DateTime | Auto | Adjustment date |

### Endorsement
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| endorsement_id | Long | PK | Unique identifier |
| endorsement_number | String | Unique, Format: END-YYYY-NNNNNN | Endorsement number |
| policy_id | Long | FK → Policy | Associated policy |
| status | Enum | DRAFT, PENDING_APPROVAL, APPROVED, EFFECTIVE | Status |
| endorsement_type | Enum | ADD_COVERAGE, REMOVE_COVERAGE, CHANGE_LIMIT, INCREASE_LIMIT, DECREASE_LIMIT | Type |
| effective_date | Date | Within policy period | Endorsement effective date |
| premium_change | Decimal(12,2) | Can be positive/negative | Premium adjustment |
| description | Text | | Change description |
| created_at | DateTime | Auto | Endorsement creation |
| approved_at | DateTime | Optional | Approval timestamp |
| effective_at | DateTime | Optional | Effective date applied |

### Payee (Vendor/Claimant)
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| payee_id | Long | PK | Unique identifier |
| payee_type | Enum | VENDOR, CLAIMANT, PROVIDER, ATTORNEY | Payee type |
| legal_name | String(255) | Required | Legal name |
| tax_id | String(11) | Encrypted | SSN (INDIVIDUAL) or EIN (BUSINESS) |
| status | Enum | PENDING_VERIFICATION, VERIFIED, BLOCKED, INACTIVE | KYC status |
| kyc_verified_date | DateTime | Optional | KYC verification date |
| address_line1 | String(255) | | Address |
| city | String(100) | | City |
| state | String(2) | | State |
| zip_code | String(10) | | ZIP |
| email | String(255) | | Contact email |
| phone | String(20) | | Contact phone |
| payment_methods | List[PaymentMethod] | 1+ required | Payment methods on file |
| created_at | DateTime | Auto | Record creation |

### PaymentMethod
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| payment_method_id | Long | PK | Unique identifier |
| payee_id | Long | FK → Payee | Associated payee |
| method_type | Enum | ACH, WIRE, CARD, STRIPE_CONNECT, GLOBAL_PAYOUTS | Payment method |
| account_number | String | Encrypted | Bank account or card number (last 4 visible) |
| routing_number | String | 9 digits (if ACH) | ACH routing number |
| account_type | Enum | CHECKING, SAVINGS | Account type |
| account_holder_name | String | | Name on account |
| swift_code | String(11) | Optional | SWIFT code for wire |
| iban | String(34) | Optional | IBAN for wire |
| is_primary | Boolean | | Default payment method |
| verified_date | DateTime | Optional | Bank verification date |
| created_at | DateTime | Auto | Record creation |

### Payment
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| payment_id | Long | PK | Unique identifier |
| claim_id | Long | FK → Claim (Optional) | Associated claim |
| policy_id | Long | FK → Policy (Optional) | Associated policy |
| payee_id | Long | FK → Payee | Payee to receive payment |
| payment_type | Enum | SETTLEMENT, REIMBURSEMENT, DISBURSEMENT, REVERSAL, REISSUE, VOID | Payment type |
| status | Enum | DRAFT, PENDING_APPROVAL, APPROVED, PROCESSING, PROCESSED, CANCELLED, FAILED | Status |
| payment_amount | Decimal(12,2) | Can be +, -, 0 | Gross payment amount |
| deduction_withholding_tax | Decimal(12,2) | >= 0 | Income tax withheld |
| deduction_fees | Decimal(12,2) | >= 0 | Medical/legal fees |
| net_payment_amount | Decimal(12,2) | = payment - deductions | Amount actually paid |
| payment_method | Enum | ACH, WIRE, CARD, STRIPE, GLOBAL | Payment method used |
| eroding_flag | Boolean | | TRUE = reduces reserve, FALSE = non-eroding |
| reserve_line_id | Long | Optional FK | Associated reserve line |
| payment_portion | Decimal(12,2) | <= net_payment_amount | If allocated to single line |
| reference_number | String | | Processor confirmation number |
| scheduled_payment_id | Long | Optional FK | If part of scheduled payment |
| created_at | DateTime | Auto | Payment creation |
| processed_at | DateTime | Optional | Processing completion |

### ReserveLine
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| reserve_line_id | Long | PK | Unique identifier |
| claim_id | Long | FK → Claim | Associated claim |
| reserve_type | Enum | MEDICAL, PROPERTY_DAMAGE, LIABILITY, SUBROGATION | Reserve category |
| estimated_amount | Decimal(12,2) | > 0 | Original estimate |
| current_balance | Decimal(12,2) | >= 0 | Current balance after payments |
| paid_to_date | Decimal(12,2) | >= 0 | Amount paid from this line |
| created_at | DateTime | Auto | Reserve creation |

### AuditLog
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| audit_id | Long | PK | Unique identifier |
| user_id | String | | User who performed action |
| user_role | String | | User's role |
| action | Enum | CREATE, UPDATE, APPROVE, PROCESS, REVERSE, VOID, DENY | Action type |
| entity_type | Enum | POLICY, CLAIM, PAYMENT, ENDORSEMENT, PREMIUM | Entity affected |
| entity_id | Long | | ID of affected entity |
| before_values | JSON | Masked PII | Before state |
| after_values | JSON | Masked PII | After state |
| ip_address | String | | IP address of user |
| timestamp | DateTime | Auto | Log timestamp |
| created_at | DateTime | Auto | Log creation |

---

## 8. Integration Requirements

### External System Integrations
1. **Stripe Connect:** OAuth token auth, connected account management, payout disbursement
2. **Global Payouts:** Multi-currency routing, compliance checks, country-specific requirements
3. **ACH/Wire Processing:** Bank file generation (NACHA), wire instruction validation
4. **Xactimate/XactAnalysis:** Estimate file parsing, line item extraction, CPT/ICD mapping
5. **Bill Review Vendors:** Pre-payment review for medical claims, fee negotiation
6. **Accounting System:** Journal entry creation, cost object tracking, reconciliation
7. **Document Management:** Policy documents, claim files, payment documentation storage
8. **Litigation Data:** Case information, attorney details, trial dates
9. **Tax ID Verification:** IRS/SSA validation for payee Tax IDs
10. **Agency Markets:** Agency data sync, policy marketplace, commission tracking

### API Integration Patterns
- **REST APIs** for all integrations (JSON payload)
- **Webhook support** for asynchronous updates (e.g., payment processor callbacks)
- **Retry logic:** Exponential backoff (3 attempts, 2^n seconds delay)
- **Circuit breaker:** Fail fast if external service unavailable (5 consecutive failures)
- **Rate limiting:** Respect processor rate limits, implement client-side throttling

---

## 9. Regulatory & Compliance Requirements

### Data Retention
- **7-year minimum** retention for all policy records post-expiration
- **7-year minimum** retention for claim records post-settlement
- **7-year minimum** retention for payment and audit records
- **Annual verification** of data retention compliance

### Privacy & Security
- **SSN/TIN masking** in UI display: XXX-XX-1234
- **Account number masking** in payment records: ****7890
- **Sensitive data encryption** at rest (AES-256)
- **HTTPS/TLS 1.2+** for all data in transit
- **No plain text storage** of passwords or keys

### Financial Compliance
- **PCI-DSS Level 1** compliance for payment processing
- **Payment card tokenization** (no card data stored)
- **ACH compliance** with NACHA standards
- **Wire transfer** compliance with banking regulations
- **1099 reporting** for vendor/contractor payments

### Accessibility Compliance
- **WCAG 2.1 Level AA** compliance for UI
- **Keyboard navigation** fully supported
- **Screen reader** compatibility (NVDA, JAWS tested)
- **Color contrast** ratio >= 4.5:1 for all text

### Audit & Control Requirements
- **Immutable audit logs** (cannot be modified or deleted)
- **Role-based access control (RBAC)** enforced
- **User session timeout** after 30 minutes of inactivity
- **Failed login lockout** after 5 attempts (15-minute duration)
- **Annual compliance audit** of security controls and data protection

---

## 10. Integration Flow Diagrams

### Policy to Claim to Payment Flow
```
Policy (Active)
    ↓
Claim (FNOL)
    ↓
Claim Investigation & Adjustment
    ↓
Claim Settlement (APPROVED)
    ↓
Payment Creation (Reserve Allocation)
    ↓
Payment Approval (if > threshold)
    ↓
Payment Processing (via Payment Method)
    ↓
Payee Receives Funds
    ↓
Audit Log Entry
```

### Payment Processing Integration
```
Payment (APPROVED)
    ↓
Determine Payment Method (Routing Rules)
    ├─→ ACH: Create NACHA file → Bank → Processing
    ├─→ Wire: Create wire instruction → Bank → Processing
    ├─→ Stripe: Call Stripe API → Processor → Payout
    └─→ Global: Route to Global Payouts → Multi-currency → Processing
    ↓
Payment Status Updates (Webhook/Polling)
    ↓
Confirmation Number Generated
    ↓
Payment Marked PROCESSED
    ↓
Payee Notified
    ↓
Audit Logged
```

---

## 11. Traceability Matrix

| User Story | Business Rule | NFR | Integration | Regulatory |
|------------|---------------|-----|-------------|------------|
| US-001 (Quote Creation) | PRM-001 to PRM-010, COV-001 to COV-003 | NFR-004, NFR-007 | - | REG-001 |
| US-002 (Bind) | POL-001, POL-002 | NFR-001, NFR-006 | - | REG-001 |
| US-009 (FNOL) | CLM-001 to CLM-005, AUD-002 | NFR-001 | Document Mgmt | REG-001 |
| US-019 (Payment Creation) | PAY-001 to PAY-010, AUD-003 | NFR-005, NFR-008 | Payment Gateway | REG-002, REG-003 |
| US-031 (RBAC) | AUD-007 | NFR-017, NFR-020 | - | REG-003 |
| US-032 (Encryption) | AUD-001 | NFR-017 to NFR-019 | - | REG-002, REG-003 |
| US-030 (Audit Trail) | AUD-001 to AUD-007 | NFR-027 to NFR-029 | - | REG-001, REG-003 |

---

## 12. Open Questions & Clarifications

1. **Premium Calculation Detail:** Should Age Factor apply only to LIFE/HEALTH policies, or to all policy types?
2. **Claim Workflows:** Are there different investigation processes for different loss types (e.g., auto collision vs. medical)?
3. **Structured Settlements:** What vendor(s) should integrate for structured settlement administration?
4. **Multi-Jurisdiction:** Should system support policies in multiple states with state-specific rating and compliance rules?
5. **Medical Claim Specifics:** Should EDI 835/837 support be prioritized for HEALTH policies?
6. **Global Payouts:** Which countries/currencies must be supported initially?
7. **Dispute Resolution:** What is the process for claim disputes/appeals?
8. **Subrogation Details:** Should subrogation be automatic (when applicable) or manual assignment?
9. **Payment Reversals:** Should reversal be supported for payments > 30 days old?
10. **Financial Statements:** Are annual GAAP-compliant financial statements a requirement?

---

## 13. Document Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Business Analyst | [To be assigned] | 2026-02-24 | [Pending] |
| Product Owner | [To be assigned] | 2026-02-24 | [Pending] |
| Compliance Officer | [To be assigned] | 2026-02-24 | [Pending] |

---

**End of Requirements Document**
