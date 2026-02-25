from sqlalchemy import String, Text, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, AuditMixin


class AuditLog(Base):
    """
    Comprehensive audit trail for all system changes.
    Tracks: who, what, when, and details of every action.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_entity_type", "entity_type"),
        Index("idx_audit_logs_entity_id", "entity_id"),
    )

    id: Mapped[int] = mapped_column(nullable=False, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    changes: Mapped[str] = mapped_column(Text, nullable=True)  # JSON diff
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[str] = mapped_column(nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="audit_logs")
