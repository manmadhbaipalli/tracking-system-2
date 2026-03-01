# Import all models for Alembic autogenerate
from app.models.base import Base
from app.models.user import User
from app.models.policy import Policy
from app.models.claim import Claim
from app.models.payment import Payment, PaymentDetail
from app.models.vendor import Vendor
from app.models.audit_log import AuditLog
from app.models.document import Document

__all__ = [
    "Base",
    "User",
    "Policy",
    "Claim",
    "Payment",
    "PaymentDetail",
    "Vendor",
    "AuditLog",
    "Document",
]
