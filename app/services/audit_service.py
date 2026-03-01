import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    session: AsyncSession,
    entity_type: str,
    entity_id: int,
    action: str,
    user_id: int,
    changes: dict = None,
    ip_address: str = None
) -> AuditLog:
    """Create an audit log entry"""
    audit_log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        changes=changes,
        ip_address=ip_address
    )
    session.add(audit_log)
    await session.commit()
    await session.refresh(audit_log)
    logger.info("Audit log created: %s %s on %s:%d by user:%d",
                action, entity_type, entity_type, entity_id, user_id)
    return audit_log
