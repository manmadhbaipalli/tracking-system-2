"""
Base model class with common functionality and audit fields.

Provides shared functionality for all database models including:
- UUID primary keys
- Automatic timestamp management
- Version control for optimistic locking
- Common utility methods
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base as DatabaseBase, GUID


class BaseModel(DatabaseBase):
    """
    Abstract base model with common fields and functionality.

    All entity models should inherit from this class to ensure consistent
    audit fields and common functionality across the application.
    """

    __abstract__ = True

    # Primary key using UUID for better security and distribution
    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the record"
    )

    # Audit timestamp fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was last updated"
    )

    # Version field for optimistic locking on critical entities
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Version number for optimistic locking"
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary representation.

        Returns:
            Dict containing all column values
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update model instance from dictionary.

        Args:
            data: Dictionary of field names and values to update
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ('id', 'created_at', 'version'):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def increment_version(self) -> None:
        """Increment version number for optimistic locking."""
        self.version += 1

    def get_audit_fields(self) -> Dict[str, Any]:
        """
        Get fields relevant for audit logging.

        Returns:
            Dict containing audit-relevant field values
        """
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version
        }


# Alias for backward compatibility with existing database configuration
Base = DatabaseBase