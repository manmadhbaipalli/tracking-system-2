"""
Claims Service Platform - Enhanced Policies API

Provides advanced policy search, CRUD operations with SSN/TIN search,
validation, and comprehensive error handling.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.core.security import get_current_user_token, require_permission, Permission
from app.models.policy import Policy
from app.schemas.policy import (
    PolicySearchRequest, PolicySearchResponse, PolicyCreate,
    PolicyUpdate, PolicyResponse, PolicySummary, PolicyValidationRequest,
    PolicyValidationResponse, BulkPolicyOperation, BulkPolicyOperationResponse
)
from app.services.policy_service import PolicyService
from app.services.audit_service import audit_service

router = APIRouter()


@router.post("/search", response_model=Dict[str, Any])
async def search_policies(
    search_request: PolicySearchRequest,
    current_user: dict = Depends(require_permission(Permission.POLICY_SEARCH)),
    db: Session = Depends(get_db)
):
    """Advanced policy search with exact/partial matching and SSN/TIN support"""
    try:
        policy_service = PolicyService(db)
        result = await policy_service.search_policies(
            criteria=search_request,
            user_id=current_user.get("user_id")
        )
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy search failed"
        )


@router.post("/search/advanced", response_model=Dict[str, Any])
async def advanced_policy_search(
    search_request: PolicySearchRequest,
    include_deleted: Optional[bool] = False,
    current_user: dict = Depends(require_permission(Permission.POLICY_SEARCH)),
    db: Session = Depends(get_db)
):
    """Multi-criteria search with performance optimization"""
    try:
        policy_service = PolicyService(db)
        result = await policy_service.search_policies(
            criteria=search_request,
            user_id=current_user.get("user_id"),
            include_deleted=include_deleted
        )
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Advanced policy search failed"
        )


@router.get("/{policy_id}", response_model=Dict[str, Any])
async def get_policy(
    policy_id: int,
    mask_pii: bool = True,
    current_user: dict = Depends(require_permission(Permission.POLICY_READ)),
    db: Session = Depends(get_db)
):
    """Get detailed policy information with optional PII masking"""
    try:
        policy_service = PolicyService(db)
        policy = await policy_service.get_policy_details(
            policy_id=policy_id,
            user_id=current_user.get("user_id"),
            mask_pii=mask_pii
        )

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )

        return policy

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve policy details"
        )


@router.post("/", response_model=Dict[str, Any])
async def create_policy(
    policy_data: PolicyCreate,
    current_user: dict = Depends(require_permission(Permission.POLICY_WRITE)),
    db: Session = Depends(get_db)
):
    """Create new policy with enhanced validation"""
    try:
        policy_service = PolicyService(db)
        policy = await policy_service.create_policy(
            policy_data=policy_data,
            user_id=current_user.get("user_id")
        )
        return policy

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create policy"
        )


@router.put("/{policy_id}", response_model=Dict[str, Any])
async def update_policy(
    policy_id: int,
    policy_data: PolicyUpdate,
    current_user: dict = Depends(require_permission(Permission.POLICY_WRITE)),
    db: Session = Depends(get_db)
):
    """Update existing policy"""
    try:
        policy_service = PolicyService(db)
        policy = await policy_service.update_policy(
            policy_id=policy_id,
            policy_data=policy_data,
            user_id=current_user.get("user_id")
        )
        return policy

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update policy"
        )


@router.get("/{policy_id}/claims", response_model=Dict[str, Any])
async def get_policy_claims(
    policy_id: int,
    status_filter: Optional[List[str]] = None,
    current_user: dict = Depends(require_permission(Permission.POLICY_READ)),
    db: Session = Depends(get_db)
):
    """Get policy claims history with optional status filtering"""
    try:
        policy_service = PolicyService(db)
        claims = await policy_service.get_policy_claims_history(
            policy_id=policy_id,
            user_id=current_user.get("user_id"),
            status_filter=status_filter
        )
        return claims

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve policy claims"
        )


@router.post("/validate", response_model=PolicyValidationResponse)
async def validate_policy_data(
    validation_request: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.POLICY_WRITE)),
    db: Session = Depends(get_db)
):
    """Validate policy data and return validation results"""
    try:
        policy_service = PolicyService(db)
        result = await policy_service.validate_policy_data(
            policy_data=validation_request,
            user_id=current_user.get("user_id")
        )
        return PolicyValidationResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy validation failed"
        )


@router.post("/search/reset", response_model=Dict[str, Any])
async def reset_search_criteria(
    current_user: dict = Depends(require_permission(Permission.POLICY_SEARCH)),
    db: Session = Depends(get_db)
):
    """Reset search criteria to default values"""
    try:
        default_criteria = PolicySearchRequest()
        return {
            "success": True,
            "default_criteria": default_criteria.dict(),
            "message": "Search criteria reset to defaults"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset search criteria"
        )


@router.post("/bulk-operation", response_model=BulkPolicyOperationResponse)
async def bulk_policy_operation(
    operation_request: BulkPolicyOperation,
    current_user: dict = Depends(require_permission(Permission.POLICY_WRITE)),
    db: Session = Depends(get_db)
):
    """Perform bulk operations on multiple policies"""
    try:
        successful = []
        failed = []

        for policy_id in operation_request.policy_ids:
            try:
                policy = db.query(Policy).filter(
                    Policy.id == policy_id,
                    Policy.is_deleted == False
                ).first()

                if not policy:
                    failed.append({
                        "policy_id": policy_id,
                        "error": "Policy not found"
                    })
                    continue

                # Perform the operation
                if operation_request.operation == "activate":
                    policy.status = "active"
                elif operation_request.operation == "deactivate":
                    policy.status = "inactive"
                elif operation_request.operation == "expire":
                    policy.status = "expired"
                elif operation_request.operation == "cancel":
                    policy.status = "cancelled"

                policy.updated_by = current_user.get("user_id")
                successful.append(policy_id)

            except Exception as e:
                failed.append({
                    "policy_id": policy_id,
                    "error": str(e)
                })

        db.commit()

        # Log bulk operation
        audit_service.log_action(
            db=db,
            user_id=current_user.get("user_id"),
            action="bulk_operation",
            table_name="policies",
            record_id=None,
            new_values={
                "operation": operation_request.operation,
                "policy_ids": operation_request.policy_ids,
                "reason": operation_request.reason
            },
            description=f"Bulk {operation_request.operation} on {len(successful)} policies"
        )

        return BulkPolicyOperationResponse(
            successful=successful,
            failed=failed,
            total_processed=len(operation_request.policy_ids),
            success_count=len(successful),
            failure_count=len(failed)
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk operation failed"
        )


@router.post("/search-vectors/update", response_model=Dict[str, Any])
async def update_search_vectors(
    current_user: dict = Depends(require_permission(Permission.POLICY_WRITE)),
    db: Session = Depends(get_db)
):
    """Bulk update search vectors for all policies"""
    try:
        policy_service = PolicyService(db)
        result = await policy_service.bulk_update_search_vectors(
            user_id=current_user.get("user_id")
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update search vectors"
        )