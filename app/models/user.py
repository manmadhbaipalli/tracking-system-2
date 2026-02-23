"""
User account and role management models.

Supports:
- User authentication and role-based access control
- User profile information
- Account status management
- Audit trail integration
"""

import uuid
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    """User roles for access control."""

    ADMIN = "admin"
    CLAIMS_ADJUSTER = "claims_adjuster"
    POLICY_AGENT = "policy_agent"
    PAYMENT_PROCESSOR = "payment_processor"
    VIEWER = "viewer"


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        return (
            self.locked_until is not None and
            self.locked_until > datetime.utcnow()
        )

    def can_access_role(self, required_role: UserRole) -> bool:
        """Check if user has required role access."""
        role_hierarchy = {
            UserRole.ADMIN: [UserRole.ADMIN, UserRole.CLAIMS_ADJUSTER, UserRole.POLICY_AGENT, UserRole.PAYMENT_PROCESSOR, UserRole.VIEWER],
            UserRole.CLAIMS_ADJUSTER: [UserRole.CLAIMS_ADJUSTER, UserRole.VIEWER],
            UserRole.POLICY_AGENT: [UserRole.POLICY_AGENT, UserRole.VIEWER],
            UserRole.PAYMENT_PROCESSOR: [UserRole.PAYMENT_PROCESSOR, UserRole.VIEWER],
            UserRole.VIEWER: [UserRole.VIEWER]
        }

        allowed_roles = role_hierarchy.get(self.role, [])
        return required_role in allowed_roles

    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts and unlock account."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def increment_failed_attempts(self) -> None:
        """Increment failed login attempts and lock if threshold exceeded."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)