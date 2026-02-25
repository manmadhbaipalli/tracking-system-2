"""SQLAlchemy models for auh-sys platform."""

from .base import Base, AuditMixin
from .user import User, Role, Permission, UserRole
from .policy import (
    Policy, Insured, Coverage, Vehicle, Location, Endorsement,
    PolicyStatus, PolicyType, CoverageType
)
from .claim import (
    Claim, ClaimAdjustment, ReserveLine, ClaimLevelPolicy, OtherCarrierInfo,
    ClaimStatus
)
from .payment import (
    Payment, Payee, PaymentMethod, PaymentDetail, PaymentDeduction,
    PaymentDocument, PaymentMethodType, PaymentStatus
)
from .audit import AuditLog
from .integration import (
    ScheduledPayment, ExternalEstimate, PaymentRoutingRule,
    TaxReportablePayment, ScheduledPaymentStatus
)

__all__ = [
    # Base
    "Base",
    "AuditMixin",
    # User & Auth
    "User",
    "Role",
    "Permission",
    "UserRole",
    # Policy
    "Policy",
    "Insured",
    "Coverage",
    "Vehicle",
    "Location",
    "Endorsement",
    "PolicyStatus",
    "PolicyType",
    "CoverageType",
    # Claim
    "Claim",
    "ClaimAdjustment",
    "ReserveLine",
    "ClaimLevelPolicy",
    "OtherCarrierInfo",
    "ClaimStatus",
    # Payment
    "Payment",
    "Payee",
    "PaymentMethod",
    "PaymentDetail",
    "PaymentDeduction",
    "PaymentDocument",
    "PaymentMethodType",
    "PaymentStatus",
    # Audit
    "AuditLog",
    # Integration
    "ScheduledPayment",
    "ExternalEstimate",
    "PaymentRoutingRule",
    "TaxReportablePayment",
    "ScheduledPaymentStatus",
]
