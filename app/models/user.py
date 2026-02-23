"""User model for authentication and user management."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text, TypeDecorator, CHAR
from sqlalchemy.sql import func

from app.database import Base


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


class User(Base):
    """
    User model for storing user account information.

    Attributes:
        id: Unique identifier for the user (UUID)
        email: User's email address (unique)
        hashed_password: Bcrypt hashed password
        is_active: Whether the user account is active
        created_at: When the user was created
        updated_at: When the user was last updated
    """

    __tablename__ = "users"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="Unique identifier for the user"
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User's email address"
    )

    hashed_password = Column(
        Text,
        nullable=False,
        doc="Bcrypt hashed password"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the user account is active"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When the user was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="When the user was last updated"
    )

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }