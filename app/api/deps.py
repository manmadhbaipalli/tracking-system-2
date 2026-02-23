"""API dependencies for database sessions, authentication, and role-based access control."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_database_session
from app.core.security import get_current_user, RoleChecker
from app.models.user import UserRole

# Database dependency
DatabaseDep = Depends(get_database_session)

# Authentication dependencies
CurrentUser = Depends(get_current_user)

# Role-based access dependencies
RequireAdmin = RoleChecker([UserRole.ADMIN.value])
RequireClaimsAdjuster = RoleChecker([UserRole.ADMIN.value, UserRole.CLAIMS_ADJUSTER.value])
RequirePolicyAgent = RoleChecker([UserRole.ADMIN.value, UserRole.POLICY_AGENT.value])
RequirePaymentProcessor = RoleChecker([UserRole.ADMIN.value, UserRole.PAYMENT_PROCESSOR.value])