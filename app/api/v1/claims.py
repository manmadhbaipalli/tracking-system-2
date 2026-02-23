"""
Claims management endpoints with policy linking, claim history, and audit trail access.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_role
from app.schemas.claim import (
    ClaimCreate,
    ClaimUpdate,
    ClaimResponse,
    ClaimSearchRequest,
    ClaimHistoryResponse
)
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: ClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "agent", "adjuster"]))
):
    """Create a new claim."""
    # TODO: Implement claim creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Claim creation not yet implemented"
    )


@router.get("/", response_model=List[ClaimResponse])
async def list_claims(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List claims with pagination and status filtering."""
    # TODO: Implement claim listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Claim listing not yet implemented"
    )


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific claim by ID."""
    # TODO: Implement claim retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Claim retrieval not yet implemented"
    )


@router.put("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: str,
    claim_data: ClaimUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "agent", "adjuster"]))
):
    """Update a specific claim."""
    # TODO: Implement claim update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Claim update not yet implemented"
    )


@router.delete("/{claim_id}")
async def delete_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Delete a specific claim."""
    # TODO: Implement claim deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Claim deletion not yet implemented"
    )


@router.get("/policy/{policy_id}/history", response_model=List[ClaimHistoryResponse])
async def get_claim_history(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get claim history for a specific policy."""
    # TODO: Implement claim history retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Claim history retrieval not yet implemented"
    )


@router.post("/search", response_model=List[ClaimResponse])
async def search_claims(
    search_request: ClaimSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search claims with multiple criteria."""
    # TODO: Implement claim search
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Claim search not yet implemented"
    )


@router.post("/{claim_id}/refer-subrogation")
async def refer_to_subrogation(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "adjuster"]))
):
    """Refer claim to subrogation."""
    # TODO: Implement subrogation referral
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Subrogation referral not yet implemented"
    )


@router.get("/{claim_id}/audit-trail")
async def get_claim_audit_trail(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a specific claim."""
    # TODO: Implement audit trail retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Audit trail retrieval not yet implemented"
    )