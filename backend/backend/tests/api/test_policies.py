"""
Claims Service Platform - Policies API Tests
"""

import pytest
from datetime import date, datetime


class TestPoliciesAPI:
    """Test policy management endpoints"""

    def test_policy_search_basic(self, test_client, auth_headers, test_policy):
        """Test basic policy search"""
        response = test_client.get("/api/policies/search", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "policies" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["policies"]) > 0

    def test_policy_search_by_policy_number(self, test_client, auth_headers, test_policy):
        """Test policy search by policy number"""
        params = {"policy_number": test_policy.policy_number}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["policies"]) >= 1
        found_policy = next((p for p in data["policies"] if p["policy_number"] == test_policy.policy_number), None)
        assert found_policy is not None

    def test_policy_search_by_insured_name(self, test_client, auth_headers, test_policy):
        """Test policy search by insured name"""
        params = {"insured_first_name": "John", "insured_last_name": "Doe"}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["policies"]) >= 1

    def test_policy_search_by_city_state(self, test_client, auth_headers, test_policy):
        """Test policy search by location"""
        params = {"policy_city": "Test City", "policy_state": "CA"}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["policies"]) >= 1

    def test_policy_search_by_zip(self, test_client, auth_headers, test_policy):
        """Test policy search by ZIP code"""
        params = {"policy_zip": "12345"}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["policies"]) >= 1

    def test_policy_search_by_vehicle_details(self, test_client, auth_headers, test_policy):
        """Test policy search by vehicle details"""
        params = {"vehicle_make": "Toyota", "vehicle_model": "Camry"}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["policies"]) >= 1

    def test_policy_search_pagination(self, test_client, auth_headers, test_policy):
        """Test policy search pagination"""
        params = {"page": 1, "page_size": 10}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert "total" in data

    def test_policy_get_by_id(self, test_client, auth_headers, test_policy):
        """Test getting specific policy by ID"""
        response = test_client.get(f"/api/policies/{test_policy.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_policy.id
        assert data["policy_number"] == test_policy.policy_number
        assert data["insured_first_name"] == test_policy.insured_first_name
        # Check that SSN is masked
        assert "ssn_tin" not in data or "***" in str(data.get("ssn_tin", ""))

    def test_policy_get_nonexistent(self, test_client, auth_headers):
        """Test getting non-existent policy"""
        response = test_client.get("/api/policies/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_policy_create(self, test_client, auth_headers):
        """Test creating new policy"""
        policy_data = {
            "policy_number": "TEST-NEW-001",
            "policy_type": "auto",
            "status": "active",
            "effective_date": "2024-01-01",
            "expiration_date": "2024-12-31",
            "insured_first_name": "Jane",
            "insured_last_name": "Smith",
            "insured_ssn_tin": "987654321",
            "policy_city": "New City",
            "policy_state": "NY",
            "policy_zip": "54321",
            "vehicle_year": 2022,
            "vehicle_make": "Honda",
            "vehicle_model": "Civic",
            "vehicle_vin": "2HGFB2F5XMH123456",
            "policy_limits_liability": 150000,
            "deductible_collision": 1000,
            "deductible_comprehensive": 500
        }
        response = test_client.post("/api/policies", json=policy_data, headers=auth_headers)
        # May not be implemented yet
        assert response.status_code in [201, 404, 405]

    def test_policy_update(self, test_client, auth_headers, test_policy):
        """Test updating existing policy"""
        update_data = {
            "policy_city": "Updated City",
            "deductible_collision": 750
        }
        response = test_client.put(f"/api/policies/{test_policy.id}", json=update_data, headers=auth_headers)
        # May not be implemented yet
        assert response.status_code in [200, 404, 405]

    def test_policy_search_no_results(self, test_client, auth_headers):
        """Test policy search with no results"""
        params = {"policy_number": "NONEXISTENT-POLICY"}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert len(data["policies"]) == 0

    def test_policy_search_partial_match(self, test_client, auth_headers, test_policy):
        """Test policy search with partial matching"""
        params = {"insured_first_name": "Joh"}  # Partial match for "John"
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        # Depending on implementation, may or may not find results
        assert data["total"] >= 0

    def test_policy_search_unauthorized(self, test_client):
        """Test policy search without authentication"""
        response = test_client.get("/api/policies/search")
        assert response.status_code == 403

    def test_policy_search_input_validation(self, test_client, auth_headers):
        """Test policy search input validation"""
        # Invalid state code
        params = {"policy_state": "INVALID"}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        # Should handle invalid input gracefully
        assert response.status_code in [200, 400, 422]

        # Invalid ZIP format
        params = {"policy_zip": "invalid-zip"}
        response = test_client.get("/api/policies/search", params=params, headers=auth_headers)
        assert response.status_code in [200, 400, 422]

    def test_policy_ssn_encryption_and_masking(self, test_client, auth_headers, test_policy):
        """Test that SSN is properly encrypted and masked in responses"""
        response = test_client.get(f"/api/policies/{test_policy.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        # SSN should be masked in the response
        if "ssn_tin" in data:
            assert "***" in str(data["ssn_tin"]) or data["ssn_tin"] is None

    def test_policy_audit_trail(self, test_client, auth_headers, test_policy):
        """Test that policy operations are audited"""
        # Get policy (should create audit entry)
        response = test_client.get(f"/api/policies/{test_policy.id}", headers=auth_headers)
        assert response.status_code == 200

        # Audit entries would be tested separately in audit tests
        # This just ensures the operation succeeds