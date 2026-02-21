"""
Claims Service Platform - Audit Service

Creates audit records for all CRUD operations with user context and data change tracking.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.audit import AuditLog
from app.core.database import get_db_context


class AuditService:
    """Service for handling audit logging across the application"""

    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[int],
        action: str,
        table_name: str,
        record_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        success: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create and save audit log entry"""

        audit_log = AuditLog.create_log(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            description=description,
            session_id=session_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            http_method=http_method,
            success=success,
            error_message=error_message,
            metadata=metadata,
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def get_audit_logs(
        db: Session,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """Retrieve audit logs with filtering"""

        query = db.query(AuditLog)

        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        if record_id:
            query = query.filter(AuditLog.record_id == record_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)

        return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

# Global audit service instance
audit_service = AuditService()