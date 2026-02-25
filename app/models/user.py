import enum
from sqlalchemy import String, Boolean, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, AuditMixin


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    AGENT = "AGENT"
    UNDERWRITER = "UNDERWRITER"
    CLAIMS_ADJUSTER = "CLAIMS_ADJUSTER"
    FINANCE_MANAGER = "FINANCE_MANAGER"
    RECOVERY_MANAGER = "RECOVERY_MANAGER"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"


class User(AuditMixin, Base):
    """Platform users with role-based access control."""
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_active", "active"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), default=UserRole.AGENT, nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Role(AuditMixin, Base):
    """Role definitions for RBAC."""
    __tablename__ = "roles"
    __table_args__ = (
        Index("idx_roles_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    permissions: Mapped[list["Permission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class Permission(AuditMixin, Base):
    """Fine-grained permissions linked to roles."""
    __tablename__ = "permissions"
    __table_args__ = (
        Index("idx_permissions_role_id", "role_id"),
        Index("idx_permissions_code", "code"),
    )

    role_id: Mapped[int] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    role: Mapped[Role] = relationship(back_populates="permissions")
