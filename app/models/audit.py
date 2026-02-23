"""
Comprehensive audit log model for tracking all data modifications.

Supports:
- Polymorphic relationships to any auditable entity
- Before/after state capture with JSON storage
- User context and timestamp tracking
- Query utilities for compliance reporting
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, GUID


class AuditLog(Base):
    """Audit log model for tracking all entity modifications."""

    __tablename__ = "audit_logs"

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        nullable=False,
        index=True
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )  # CREATE, UPDATE, DELETE
    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    after_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("users.id"),
        nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # Support IPv6
        nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    changes_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationship to user (if available)
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        lazy="select"
    )

    # Composite indexes for efficient querying
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user_time", "user_id", "timestamp"),
        Index("idx_audit_action_time", "action", "timestamp"),
    )

    def __repr__(self) -> str:
        return (f"<AuditLog(id={self.id}, entity_type={self.entity_type}, "
                f"entity_id={self.entity_id}, action={self.action})>")

    @classmethod
    def create_log(
        cls,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        user_id: Optional[uuid.UUID] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> "AuditLog":
        """
        Create a new audit log entry.

        Args:
            entity_type: Type of entity being audited (e.g., "Policy", "Claim")
            entity_id: ID of the entity being audited
            action: Action performed (CREATE, UPDATE, DELETE)
            user_id: ID of user performing the action
            before_state: Entity state before the action
            after_state: Entity state after the action
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request ID for correlation

        Returns:
            New AuditLog instance
        """
        changes_summary = cls._generate_changes_summary(before_state, after_state)

        return cls(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            changes_summary=changes_summary,
            timestamp=datetime.utcnow()
        )

    @staticmethod
    def _generate_changes_summary(
        before_state: Optional[Dict[str, Any]],
        after_state: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate a human-readable summary of changes."""
        if not before_state or not after_state:
            return None

        changes = []
        all_keys = set(before_state.keys()) | set(after_state.keys())

        for key in all_keys:
            before_val = before_state.get(key)
            after_val = after_state.get(key)

            if before_val != after_val:
                if before_val is None:
                    changes.append(f"Added {key}: {after_val}")
                elif after_val is None:
                    changes.append(f"Removed {key}")
                else:
                    changes.append(f"Changed {key}: {before_val} → {after_val}")

        return "; ".join(changes) if changes else None

    def get_field_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed field changes.

        Returns:
            Dictionary mapping field names to before/after values
        """
        if not self.before_state or not self.after_state:
            return {}

        changes = {}
        all_keys = set(self.before_state.keys()) | set(self.after_state.keys())

        for key in all_keys:
            before_val = self.before_state.get(key)
            after_val = self.after_state.get(key)

            if before_val != after_val:
                changes[key] = {
                    "before": before_val,
                    "after": after_val
                }

        return changes