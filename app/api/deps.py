"""API dependencies for database sessions, authentication, audit context, and role-based access control."""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database_session, DatabaseSessionManager
from app.core.security import get_current_user, get_current_active_user, RoleChecker
from app.core.config import settings
from app.models.user import User, UserRole


# Database dependencies
DatabaseDep = Depends(get_database_session)


async def get_database_manager() -> DatabaseSessionManager:
    """Get database session manager for complex operations."""
    return DatabaseSessionManager()


DatabaseManagerDep = Depends(get_database_manager)

# Authentication dependencies
CurrentUser = Depends(get_current_user)
CurrentActiveUser = Depends(get_current_active_user)


class AuditContext:
    """Audit context for tracking user actions and changes."""

    def __init__(
        self,
        user: User,
        request: Request,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
    ):
        self.user_id = user.id
        self.user_email = user.email
        self.user_role = user.role
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.timestamp = datetime.utcnow()
        self.ip_address = request.client.host if request.client else None
        self.user_agent = request.headers.get("User-Agent")
        self.session_id = request.headers.get("X-Session-ID")
        self.changes: Dict[str, Any] = {}
        self.old_values: Dict[str, Any] = {}
        self.new_values: Dict[str, Any] = {}

    def set_entity_info(self, entity_type: str, entity_id: uuid.UUID):
        """Set entity information for the audit context."""
        self.entity_type = entity_type
        self.entity_id = entity_id

    def set_action(self, action: str):
        """Set the action being performed."""
        self.action = action

    def record_change(self, field: str, old_value: Any, new_value: Any):
        """Record a field change."""
        self.old_values[field] = old_value
        self.new_values[field] = new_value
        self.changes[field] = {"old": old_value, "new": new_value}

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit context to dictionary for logging."""
        return {
            "user_id": str(self.user_id),
            "user_email": self.user_email,
            "user_role": self.user_role.value if hasattr(self.user_role, "value") else str(self.user_role),
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "changes": self.changes,
            "old_values": self.old_values,
            "new_values": self.new_values,
        }


async def get_audit_context(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> AuditContext:
    """Get audit context for the current request."""
    return AuditContext(user=current_user, request=request)


AuditContextDep = Depends(get_audit_context)


class SecurityContext:
    """Enhanced security context with additional validation."""

    def __init__(self, user: User, request: Request):
        self.user = user
        self.request = request
        self.ip_address = request.client.host if request.client else None
        self.user_agent = request.headers.get("User-Agent")
        self.session_id = request.headers.get("X-Session-ID")
        self.timestamp = datetime.utcnow()

    def validate_session(self) -> bool:
        """Validate user session (can be extended with session store)."""
        # Basic validation - can be enhanced with Redis session store
        if not self.user.is_active:
            return False
        return True

    def check_ip_restriction(self) -> bool:
        """Check if IP address is allowed (can be enhanced with IP whitelist)."""
        # Default to allow all - can be enhanced with IP restrictions
        return True

    def validate_user_agent(self) -> bool:
        """Validate user agent for security (can detect suspicious patterns)."""
        if not self.user_agent:
            return False
        # Basic validation - can be enhanced with pattern matching
        return len(self.user_agent) > 10  # Simple check


async def get_security_context(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> SecurityContext:
    """Get enhanced security context for the current request."""
    security_ctx = SecurityContext(user=current_user, request=request)

    # Perform security validations
    if not security_ctx.validate_session():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    if not security_ctx.check_ip_restriction():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address"
        )

    if not security_ctx.validate_user_agent():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user agent"
        )

    return security_ctx


SecurityContextDep = Depends(get_security_context)


class EnhancedRoleChecker(RoleChecker):
    """Enhanced role checker with additional validation and logging."""

    def __init__(self, allowed_roles: list[str], require_active: bool = True):
        super().__init__(allowed_roles)
        self.require_active = require_active

    def __call__(self,
                 current_user: User = Depends(get_current_user),
                 request: Request = None):
        """Enhanced role checking with additional validations."""

        # Check if user is active
        if self.require_active and not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        # Check role permissions
        user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )

        return current_user


# Enhanced role-based access dependencies
RequireAdmin = EnhancedRoleChecker([UserRole.ADMIN.value])
RequireClaimsAdjuster = EnhancedRoleChecker([
    UserRole.ADMIN.value,
    UserRole.ADJUSTER.value
])
RequirePolicyAgent = EnhancedRoleChecker([
    UserRole.ADMIN.value,
    UserRole.AGENT.value
])
RequirePaymentProcessor = EnhancedRoleChecker([
    UserRole.ADMIN.value,
    UserRole.ADJUSTER.value
])

# Combined permissions for common scenarios
RequireClaimsOrAdmin = EnhancedRoleChecker([
    UserRole.ADMIN.value,
    UserRole.CLAIMS_ADJUSTER.value
])

RequirePolicyOrAdmin = EnhancedRoleChecker([
    UserRole.ADMIN.value,
    UserRole.POLICY_AGENT.value
])

RequirePaymentOrAdmin = EnhancedRoleChecker([
    UserRole.ADMIN.value,
    UserRole.PAYMENT_PROCESSOR.value
])

# Multi-role permissions
RequireClaimsOrPayment = EnhancedRoleChecker([
    UserRole.ADMIN.value,
    UserRole.CLAIMS_ADJUSTER.value,
    UserRole.PAYMENT_PROCESSOR.value
])

RequireAnyAgent = EnhancedRoleChecker([
    UserRole.ADMIN.value,
    UserRole.CLAIMS_ADJUSTER.value,
    UserRole.POLICY_AGENT.value,
    UserRole.PAYMENT_PROCESSOR.value
])


# Performance monitoring dependency
class PerformanceTracker:
    """Track API endpoint performance."""

    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self.start_time = datetime.utcnow()

    def complete(self) -> float:
        """Mark operation as complete and return duration."""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        return duration


def get_performance_tracker(endpoint_name: str) -> PerformanceTracker:
    """Get performance tracker for an endpoint."""
    return PerformanceTracker(endpoint_name)