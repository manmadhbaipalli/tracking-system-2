"""
Claims Service Platform - Audit Model

Comprehensive audit trail for all operations with user, timestamp, action type, and changed data.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class AuditAction(enum.Enum):
    """Audit action types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    SEARCH = "search"
    EXPORT = "export"
    APPROVE = "approve"
    REJECT = "reject"
    PROCESS = "process"
    VOID = "void"
    REVERSE = "reverse"


class AuditLog(Base):
    """Audit log model for tracking all system operations"""

    __tablename__ = "audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # User and session information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(255), index=True)
    request_id = Column(String(255), index=True)

    # Action details
    action = Column(String(50), nullable=False, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(50), index=True)  # String to handle different ID types

    # Request information
    endpoint = Column(String(500))
    http_method = Column(String(10))
    ip_address = Column(String(45))  # Supports IPv6
    user_agent = Column(String(500))

    # Data changes
    old_values = Column(JSON)  # JSON field for before data
    new_values = Column(JSON)  # JSON field for after data
    changed_fields = Column(JSON)  # Array of changed field names

    # Additional context
    description = Column(Text)
    metadata = Column(JSON)  # Additional contextual data

    # Result information
    success = Column(String(10), default="success")  # success, failure, partial
    error_message = Column(Text)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', table='{self.table_name}', user_id={self.user_id})>"

    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "action": self.action,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "endpoint": self.endpoint,
            "http_method": self.http_method,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "changed_fields": self.changed_fields,
            "description": self.description,
            "metadata": self.metadata,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def create_log(
        cls,
        user_id: int = None,
        action: str = None,
        table_name: str = None,
        record_id: str = None,
        old_values: dict = None,
        new_values: dict = None,
        description: str = None,
        session_id: str = None,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        endpoint: str = None,
        http_method: str = None,
        success: str = "success",
        error_message: str = None,
        metadata: dict = None,
    ):
        """Create a new audit log entry"""

        # Calculate changed fields
        changed_fields = []
        if old_values and new_values:
            for key in new_values.keys():
                if key in old_values:
                    if old_values[key] != new_values[key]:
                        changed_fields.append(key)
                else:
                    changed_fields.append(key)

        return cls(
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            action=action,
            table_name=table_name,
            record_id=str(record_id) if record_id else None,
            endpoint=endpoint,
            http_method=http_method,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            description=description,
            metadata=metadata,
            success=success,
            error_message=error_message,
        )

    def get_summary(self) -> str:
        """Get human-readable audit log summary"""
        user_info = f"User {self.user_id}" if self.user_id else "System"
        action_desc = self.action.replace("_", " ").title()

        summary = f"{user_info} performed {action_desc} on {self.table_name}"

        if self.record_id:
            summary += f" (ID: {self.record_id})"

        if self.changed_fields:
            summary += f" - Changed fields: {', '.join(self.changed_fields)}"

        return summary

    def is_sensitive_operation(self) -> bool:
        """Check if this audit log represents a sensitive operation"""
        sensitive_actions = ["delete", "approve", "process", "void", "reverse"]
        sensitive_tables = ["payments", "users"]

        return (
            self.action in sensitive_actions or
            self.table_name in sensitive_tables or
            (self.changed_fields and any("password" in field.lower() for field in self.changed_fields))
        )

    def mask_sensitive_data(self):
        """Mask sensitive data in audit log for display"""
        if self.old_values:
            self.old_values = self._mask_dict(self.old_values)

        if self.new_values:
            self.new_values = self._mask_dict(self.new_values)

    def _mask_dict(self, data: dict) -> dict:
        """Mask sensitive fields in dictionary"""
        if not isinstance(data, dict):
            return data

        sensitive_fields = [
            "password", "hashed_password", "ssn", "tin", "account_number",
            "routing_number", "card_number", "card_cvv", "api_key"
        ]

        masked_data = data.copy()
        for field in sensitive_fields:
            if field in masked_data:
                masked_data[field] = "***MASKED***"

        return masked_data

    @property
    def age_in_days(self) -> int:
        """Get age of audit log in days"""
        if not self.timestamp:
            return 0

        now = datetime.utcnow().replace(tzinfo=self.timestamp.tzinfo)
        return (now - self.timestamp).days

    def should_be_archived(self, retention_days: int = 2555) -> bool:
        """Check if audit log should be archived based on retention policy"""
        return self.age_in_days > retention_days