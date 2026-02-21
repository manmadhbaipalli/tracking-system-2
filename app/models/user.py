"""User database model"""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from ..database import Base


class User(Base):
    """User model for authentication and profile management"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User email address (unique)"
    )
    password_hash = Column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="User account status"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Account creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last update timestamp"
    )

    def __repr__(self) -> str:
        """String representation of User model"""
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"