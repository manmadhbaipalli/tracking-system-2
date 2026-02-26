from sqlalchemy import String, Boolean, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, AuditMixin
from .enums import Role


class User(AuditMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_active", "active"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, values_callable=lambda e: [x.value for x in e]),
        default=Role.USER,
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
