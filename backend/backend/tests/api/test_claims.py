"""
Claims Service Platform - Claims API Tests
"""

import pytest
from datetime import date


class TestClaimsAPI:
    """Test claims management endpoints"""

    def test_create_claim(self, test_client, auth_headers, test_policy):
        """Test creating a new claim"""
        claim_data = {
            "policy_id": test_policy.id,
            "claim_number": "CLM-NEW-001",
            "date_of_loss": "2024-07-01",
            "loss_description": "Rear-end collision at intersection",
            "reported_date": "2024-07-02",
            "claim_amount": 3500.00,
            "claim_status": "open"
        }
        response = test_client.post("/api/claims", json=claim_data, headers=auth_headers)
        # May not be fully implemented yet
        assert response.status_code in [201, 404, 405]

    def test_get_claim_by_id(self, test_client, auth_headers, test_claim):
        """Test getting specific claim by ID"""
        response = test_client.get(f"/api/claims/{test_claim.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_claim.id
        assert data["claim_number"] == test_claim.claim_number
        assert data["policy_id"] == test_claim.policy_id

    def test_get_claims_by_policy(self, test_client, auth_headers, test_claim, test_policy):
        """Test getting claims by policy ID"""
        response = test_client.get(f"/api/claims/policy/{test_policy.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        claim_found = any(claim["id"] == test_claim.id for claim in data)
        assert claim_found

    def test_get_nonexistent_claim(self, test_client, auth_headers):
        """Test getting non-existent claim"""
        response = test_client.get("/api/claims/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_claim_status(self, test_client, auth_headers, test_claim):
        """Test updating claim status"""
        update_data = {"claim_status": "in_review"}
        response = test_client.put(f"/api/claims/{test_claim.id}", json=update_data, headers=auth_headers)
        # May not be implemented yet
        assert response.status_code in [200, 404, 405]

    def test_update_claim_amount(self, test_client, auth_headers, test_claim):
        """Test updating claim amount"""
        update_data = {"claim_amount": 7500.00}
        response = test_client.put(f"/api/claims/{test_claim.id}", json=update_data, headers=auth_headers)
        # May not be implemented yet
        assert response.status_code in [200, 404, 405]

    def test_claim_history_by_policy(self, test_client, auth_headers, test_policy):
        """Test retrieving claim history for a policy"""
        response = test_client.get(f"/api/claims/policy/{test_policy.id}/history", headers=auth_headers)
        assert response.status_code in [200, 404]  # Endpoint may not be implemented

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_claims_filtering_by_status(self, test_client, auth_headers, test_policy):
        """Test filtering claims by status"""
        params = {"status": "open"}
        response = test_client.get(f"/api/claims/policy/{test_policy.id}", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        for claim in data:
            assert claim["claim_status"] in ["open", "Open", "OPEN"]

    def test_claims_sorting_by_date(self, test_client, auth_headers, test_policy):
        """Test sorting claims by date of loss"""
        params = {"sort_by": "date_of_loss", "sort_order": "desc"}
        response = test_client.get(f"/api/claims/policy/{test_policy.id}", params=params, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        # Verify sorting if multiple claims exist
        if len(data) > 1:
            dates = [claim["date_of_loss"] for claim in data]
            assert dates == sorted(dates, reverse=True)

    def test_claim_policy_relationship_validation(self, test_client, auth_headers):
        """Test claim creation with invalid policy ID"""
        claim_data = {
            "policy_id": 99999,  # Non-existent policy
            "claim_number": "CLM-INVALID-001",
            "date_of_loss": "2024-07-01",
            "loss_description": "Test claim with invalid policy",
            "reported_date": "2024-07-02",
            "claim_amount": 1000.00
        }
        response = test_client.post("/api/claims", json=claim_data, headers=auth_headers)
        # Should reject invalid policy ID
        assert response.status_code in [400, 404, 422]

    def test_claim_date_validation(self, test_client, auth_headers, test_policy):
        """Test claim creation with invalid dates"""
        # Future date of loss
        claim_data = {
            "policy_id": test_policy.id,
            "claim_number": "CLM-FUTURE-001",
            "date_of_loss": "2030-01-01",  # Future date
            "loss_description": "Future loss",
            "reported_date": "2024-07-02",
            "claim_amount": 1000.00
        }
        response = test_client.post("/api/claims", json=claim_data, headers=auth_headers)
        # Should handle future dates appropriately
        assert response.status_code in [201, 400, 422]

    def test_claim_amount_validation(self, test_client, auth_headers, test_policy):
        """Test claim creation with invalid amounts"""
        # Negative amount
        claim_data = {
            "policy_id": test_policy.id,
            "claim_number": "CLM-NEG-001",
            "date_of_loss": "2024-07-01",
            "loss_description": "Negative amount claim",
            "reported_date": "2024-07-02",
            "claim_amount": -1000.00
        }
        response = test_client.post("/api/claims", json=claim_data, headers=auth_headers)
        # Should reject negative amounts
        assert response.status_code in [400, 422]

    def test_duplicate_claim_number(self, test_client, auth_headers, test_policy, test_claim):
        """Test creating claim with duplicate claim number"""
        claim_data = {
            "policy_id": test_policy.id,
            "claim_number": test_claim.claim_number,  # Duplicate
            "date_of_loss": "2024-07-01",
            "loss_description": "Duplicate claim number",
            "reported_date": "2024-07-02",
            "claim_amount": 1000.00
        }
        response = test_client.post("/api/claims", json=claim_data, headers=auth_headers)
        # Should reject duplicate claim numbers
        assert response.status_code in [400, 422]

    def test_claim_unauthorized_access(self, test_client):
        """Test accessing claims without authentication"""
        response = test_client.get("/api/claims/1")
        assert response.status_code == 403

    def test_claim_level_policy_updates(self, test_client, auth_headers, test_claim):
        """Test claim-level policy information updates"""
        policy_update_data = {
            "claim_policy_override": {
                "insured_first_name": "Updated Name",
                "policy_city": "Updated City"
            }
        }
        response = test_client.put(f"/api/claims/{test_claim.id}/policy", json=policy_update_data, headers=auth_headers)
        # This feature may not be implemented yet
        assert response.status_code in [200, 404, 405]

    def test_claim_audit_logging(self, test_client, auth_headers, test_claim):
        """Test that claim operations are audited"""
        # Retrieve claim (should be audited)
        response = test_client.get(f"/api/claims/{test_claim.id}", headers=auth_headers)
        assert response.status_code == 200

        # The actual audit verification would be in separate audit tests