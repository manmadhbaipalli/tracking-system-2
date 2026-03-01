from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # policy, claim, payment, user
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)  # create, update, delete, view
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    changes = Column(JSON, nullable=True)  # Before/after values
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
