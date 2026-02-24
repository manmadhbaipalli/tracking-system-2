from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, AuditMixin


class RequestLog(AuditMixin, Base):
    __tablename__ = "request_logs"
    __table_args__ = (
        Index("idx_request_logs_correlation_id", "correlation_id"),
        Index("idx_request_logs_created_at", "created_at"),
        Index("idx_request_logs_user_id", "user_id"),
    )

    correlation_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationship to User (optional - for authenticated requests only)
    user: Mapped["User | None"] = relationship("User", back_populates="request_logs")