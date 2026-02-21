"""
Claims Service Platform - User Model

User authentication and role management model with hashed passwords and audit trail links.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base
from app.core.security import UserRole


class UserStatus(enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Authentication fields
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    full_name = Column(String(100), nullable=False)

    # Role and permissions
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.PENDING)

    # Contact information
    phone = Column(String(20))
    department = Column(String(100))
    title = Column(String(100))

    # Security and session management
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True))

    # Account settings
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))

    # API access
    api_key_hash = Column(String(255))
    api_key_created_at = Column(DateTime(timezone=True))

    # Preferences
    preferences = Column(Text)  # JSON string for user preferences
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

    # Relationships
    audit_logs = relationship(
        "AuditLog",
        foreign_keys="AuditLog.user_id",
        back_populates="user"
    )

    policies_created = relationship(
        "Policy",
        foreign_keys="Policy.created_by",
        back_populates="creator"
    )

    claims_created = relationship(
        "Claim",
        foreign_keys="Claim.created_by",
        back_populates="creator"
    )

    payments_created = relationship(
        "Payment",
        foreign_keys="Payment.created_by",
        back_populates="creator"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self):
        """Convert user object to dictionary (excluding sensitive data)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role.value if self.role else None,
            "status": self.status.value if self.status else None,
            "phone": self.phone,
            "department": self.department,
            "title": self.title,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "timezone": self.timezone,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN

    @property
    def is_account_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.account_locked_until:
            return False
        return datetime.utcnow() < self.account_locked_until.replace(tzinfo=None)

    def can_perform_action(self, permission: str) -> bool:
        """Check if user can perform specific action based on role"""
        from app.core.security import ROLE_PERMISSIONS, Permission

        try:
            perm = Permission(permission)
            user_permissions = ROLE_PERMISSIONS.get(self.role, [])
            return perm in user_permissions
        except ValueError:
            return False

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = func.now()
        self.failed_login_attempts = 0

    def increment_failed_login(self):
        """Increment failed login counter"""
        self.failed_login_attempts += 1

        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.account_locked_until = func.now() + func.interval('30 minutes')

    def unlock_account(self):
        """Unlock user account"""
        self.failed_login_attempts = 0
        self.account_locked_until = None

    def update_password_changed(self):
        """Update password changed timestamp"""
        self.password_changed_at = func.now()

    def set_preferences(self, preferences: dict):
        """Set user preferences as JSON"""
        import json
        self.preferences = json.dumps(preferences)

    def get_preferences(self) -> dict:
        """Get user preferences as dictionary"""
        import json
        if self.preferences:
            try:
                return json.loads(self.preferences)
            except json.JSONDecodeError:
                return {}
        return {}

    def generate_full_name(self):
        """Generate full name from first and last name"""
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        elif self.first_name:
            self.full_name = self.first_name
        elif self.last_name:
            self.full_name = self.last_name
        else:
            self.full_name = self.username