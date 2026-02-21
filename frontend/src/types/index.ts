/**
 * TypeScript type definitions for the Claims Service Platform
 */

export interface Policy {
  id: number;
  policy_number: string;
  policy_type: string;
  status: string;
  effective_date: string;
  expiration_date: string;
  insured_first_name: string;
  insured_last_name: string;
  insured_full_name: string;
  ssn?: string; // Masked
  tin?: string; // Masked
  organization_name?: string;
  city: string;
  state: string;
  zip_code: string;
  vehicle_year?: number;
  vehicle_make?: string;
  vehicle_model?: string;
  vehicle_vin?: string;
  is_active: boolean;
  days_until_expiration: number;
  created_at: string;
  updated_at: string;
}

export interface PolicySearchCriteria {
  policy_number?: string;
  insured_first_name?: string;
  insured_last_name?: string;
  policy_type?: string;
  policy_city?: string;
  policy_state?: string;
  policy_zip?: string;
  ssn_tin?: string;
  organization_name?: string;
  search_type: 'exact' | 'partial';
  page: number;
  page_size: number;
}

export interface PolicySearchResult {
  policies: Policy[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  search_criteria: PolicySearchCriteria;
}

export interface Claim {
  id: number;
  claim_number: string;
  policy_id: number;
  date_of_loss?: string;
  claim_status: string;
  claim_type?: string;
  total_incurred?: number;
  total_paid?: number;
  total_reserve?: number;
  has_policy_override: boolean;
  override_indicator?: string;
  days_open: number;
  adjuster_name?: string;
}

export interface ClaimHistoryResult {
  claims: Claim[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_claim_overrides: boolean;
  filters_applied: {
    policy_id?: number;
    status_filter: string[];
  };
}

export interface Payment {
  id: number;
  claim_id: number;
  amount: number;
  payment_method: string;
  status: string;
  transaction_id?: string;
  reference_number?: string;
  payee_name?: string;
  created_at: string;
}

export interface PaymentMethod {
  type: 'ach' | 'wire' | 'card' | 'stripe' | 'check';
  name: string;
  description: string;
  enabled: boolean;
}

export interface PaymentProcessRequest {
  claim_id: number;
  payment_method: string;
  amount: number;
  recipients: PaymentRecipient[];
  reserve_allocations: ReserveAllocation[];
  tax_reportable: boolean;
  documentation: DocumentReference[];
}

export interface PaymentRecipient {
  name: string;
  payment_method: Record<string, any>;
  amount: number;
  tax_id?: string;
  is_joint_payee: boolean;
}

export interface ReserveAllocation {
  reserve_line: string;
  amount: number;
  eroding: boolean;
}

export interface DocumentReference {
  type: string;
  reference: string;
  description?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface SearchFilters {
  status?: string[];
  policy_type?: string;
  state?: string;
  date_range?: {
    from: string;
    to: string;
  };
}

export interface User {
  user_id: number;
  username: string;
  email: string;
  role: string;
  permissions: string[];
}