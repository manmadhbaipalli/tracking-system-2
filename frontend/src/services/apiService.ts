/**
 * API Service for Claims Platform Frontend
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  Policy,
  PolicySearchCriteria,
  PolicySearchResult,
  ClaimHistoryResult,
  Payment,
  PaymentProcessRequest,
  PaymentMethod,
  ValidationResult,
  ApiResponse
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for adding auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for handling common errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Policy API methods
  async searchPolicies(criteria: PolicySearchCriteria): Promise<PolicySearchResult> {
    const response = await this.api.post('/policies/search', criteria);
    return response.data;
  }

  async advancedPolicySearch(criteria: PolicySearchCriteria, includeDeleted: boolean = false): Promise<PolicySearchResult> {
    const response = await this.api.post(`/policies/search/advanced?include_deleted=${includeDeleted}`, criteria);
    return response.data;
  }

  async getPolicyDetails(policyId: number, maskPii: boolean = true): Promise<Policy> {
    const response = await this.api.get(`/policies/${policyId}?mask_pii=${maskPii}`);
    return response.data;
  }

  async createPolicy(policyData: Partial<Policy>): Promise<Policy> {
    const response = await this.api.post('/policies/', policyData);
    return response.data;
  }

  async updatePolicy(policyId: number, policyData: Partial<Policy>): Promise<Policy> {
    const response = await this.api.put(`/policies/${policyId}`, policyData);
    return response.data;
  }

  async getPolicyClaims(policyId: number, statusFilter?: string[]): Promise<ClaimHistoryResult> {
    let url = `/policies/${policyId}/claims`;
    if (statusFilter && statusFilter.length > 0) {
      const params = new URLSearchParams();
      statusFilter.forEach(status => params.append('status_filter', status));
      url += `?${params.toString()}`;
    }
    const response = await this.api.get(url);
    return response.data;
  }

  async validatePolicyData(policyData: Partial<Policy>): Promise<ValidationResult> {
    const response = await this.api.post('/policies/validate', policyData);
    return response.data;
  }

  async resetSearchCriteria(): Promise<{ success: boolean; default_criteria: PolicySearchCriteria }> {
    const response = await this.api.post('/policies/search/reset');
    return response.data;
  }

  // Claims API methods
  async getClaimsHistory(
    policyId?: number,
    statusFilter?: string[],
    page: number = 1,
    pageSize: number = 25
  ): Promise<ClaimHistoryResult> {
    let url = '/claims/history';
    const params = new URLSearchParams();

    if (policyId) params.append('policy_id', policyId.toString());
    if (statusFilter) statusFilter.forEach(status => params.append('status_filter', status));
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());

    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    const response = await this.api.get(url);
    return response.data;
  }

  async createClaimPolicyOverride(claimId: number, policyData: Partial<Policy>): Promise<ApiResponse<void>> {
    const response = await this.api.post(`/claims/${claimId}/policy-override`, policyData);
    return response.data;
  }

  async getClaimPolicyOverride(claimId: number): Promise<any> {
    const response = await this.api.get(`/claims/${claimId}/policy-override`);
    return response.data;
  }

  async manageSubrogation(claimId: number, subrogationData: any): Promise<ApiResponse<void>> {
    const response = await this.api.post(`/claims/${claimId}/subrogation`, subrogationData);
    return response.data;
  }

  async calculateSettlement(claimId: number, settlementParams: any): Promise<any> {
    const response = await this.api.post(`/claims/${claimId}/settlement`, settlementParams);
    return response.data;
  }

  // Payment API methods
  async processPayment(paymentRequest: PaymentProcessRequest): Promise<any> {
    const response = await this.api.post('/payments/process', paymentRequest);
    return response.data;
  }

  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await this.api.get('/payments/methods');
    return response.data;
  }

  async allocateReserves(claimId: number, allocations: any[]): Promise<any> {
    const response = await this.api.post(`/payments/${claimId}/allocate-reserves`, { allocations });
    return response.data;
  }

  async processSettlement(claimId: number, settlementData: any): Promise<any> {
    const response = await this.api.post(`/payments/${claimId}/settlement`, settlementData);
    return response.data;
  }

  // Authentication methods
  async login(username: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const response = await this.api.post('/auth/login', { username, password });
    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    return response.data;
  }

  async logout(): Promise<void> {
    localStorage.removeItem('access_token');
  }

  async getCurrentUser(): Promise<any> {
    const response = await this.api.get('/auth/me');
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;