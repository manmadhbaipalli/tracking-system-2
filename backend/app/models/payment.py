"""
Claims Service Platform - Payment Model

Payment and disbursement models with multiple payment methods, lifecycle tracking, and compliance.
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Decimal, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum
from decimal import Decimal as PyDecimal

from app.core.database import Base, EncryptedText, EncryptedString
from app.utils.validators import validate_payment_amount, validate_routing_number, validate_account_number


class PaymentStatus(enum.Enum):
    """Payment status enumeration"""
    CREATED = "created"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VOIDED = "voided"
    REVERSED = "reversed"
    REISSUED = "reissued"


class PaymentMethod(enum.Enum):
    """Payment method enumeration"""
    ACH = "ach"
    WIRE = "wire"
    CHECK = "check"
    CARD = "card"
    STRIPE_CONNECT = "stripe_connect"
    GLOBAL_PAYOUT = "global_payout"
    CASH = "cash"
    MANUAL = "manual"


class PaymentType(enum.Enum):
    """Payment type enumeration"""
    CLAIM_PAYMENT = "claim_payment"
    SETTLEMENT = "settlement"
    DEDUCTIBLE_REFUND = "deductible_refund"
    RECOVERY = "recovery"
    EXPENSE_REIMBURSEMENT = "expense_reimbursement"
    MEDICAL_PAYMENT = "medical_payment"
    LEGAL_EXPENSE = "legal_expense"
    EXPERT_FEES = "expert_fees"
    COURT_COSTS = "court_costs"
    ADMINISTRATIVE = "administrative"


class ReserveLineType(enum.Enum):
    """Reserve line type enumeration"""
    PROPERTY_DAMAGE = "property_damage"
    BODILY_INJURY = "bodily_injury"
    MEDICAL_PAYMENTS = "medical_payments"
    LEGAL_EXPENSE = "legal_expense"
    LOSS_ADJUSTMENT_EXPENSE = "loss_adjustment_expense"
    UNINSURED_MOTORIST = "uninsured_motorist"
    PERSONAL_INJURY_PROTECTION = "personal_injury_protection"
    COMPREHENSIVE = "comprehensive"
    COLLISION = "collision"


class Payment(Base):
    """Payment model with encrypted payment details and lifecycle tracking"""

    __tablename__ = "payments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Payment identification
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    external_payment_id = Column(String(100), index=True)  # ID from external processor
    batch_id = Column(String(50), index=True)

    # Relationships
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False, index=True)

    # Payment basics
    payment_method = Column(String(30), nullable=False, index=True)
    payment_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=PaymentStatus.CREATED.value, index=True)

    # Financial information
    amount = Column(Decimal(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Decimal(10, 6), default=1.0)

    # Payment dates
    payment_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, index=True)
    processed_date = Column(Date, index=True)
    cleared_date = Column(Date, index=True)

    # Payee information
    payee_name = Column(String(200), nullable=False)
    payee_type = Column(String(50))  # individual, business, medical_provider, attorney, etc.
    payee_tax_id = Column(EncryptedString(255))  # SSN or EIN
    payee_address = Column(JSON)  # Address object

    # Joint payees (for insurance payments with multiple parties)
    joint_payees = Column(JSON)  # Array of additional payee information

    # Payment method specific details (encrypted)
    payment_details = Column(EncryptedText)  # JSON with payment method specific info

    # ACH/Wire specific fields
    bank_name = Column(String(100))
    routing_number = Column(EncryptedString(15))
    account_number = Column(EncryptedString(25))
    account_type = Column(String(20))  # checking, savings
    swift_code = Column(EncryptedString(15))
    iban = Column(EncryptedString(50))

    # Check specific fields
    check_number = Column(String(20))
    check_memo = Column(String(100))

    # Card specific fields
    card_last_four = Column(String(4))
    card_type = Column(String(20))

    # Reserve line allocation
    reserve_allocations = Column(JSON)  # Array of reserve line allocations
    is_eroding = Column(Boolean, default=True)  # Whether payment erodes reserves

    # Tax and compliance
    is_tax_reportable = Column(Boolean, default=False)
    tax_year = Column(Integer)
    withholding_amount = Column(Decimal(10, 2), default=0)
    tax_form_type = Column(String(20))  # 1099-MISC, 1099-NEC, etc.

    # Settlement and negotiation
    is_settlement_payment = Column(Boolean, default=False)
    settlement_percentage = Column(Decimal(5, 2))  # Percentage of demand/reserve
    includes_interest = Column(Boolean, default=False)
    interest_amount = Column(Decimal(10, 2))

    # Medical payments specific
    medical_provider_npi = Column(String(20))  # National Provider Identifier
    medical_procedure_codes = Column(JSON)  # Array of CPT codes
    medical_diagnosis_codes = Column(JSON)  # Array of ICD codes

    # Document attachments
    supporting_documents = Column(JSON)  # Array of document references
    remittance_advice = Column(JSON)  # Remittance details for medical payments

    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approval_date = Column(DateTime(timezone=True))
    approval_notes = Column(Text)

    # Processing and tracking
    processor_reference = Column(String(100))
    processing_fee = Column(Decimal(8, 2))
    failure_reason = Column(String(500))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Void and reversal tracking
    original_payment_id = Column(Integer, ForeignKey("payments.id"))
    voided_payment_id = Column(Integer, ForeignKey("payments.id"))
    void_reason = Column(String(500))
    reversal_reason = Column(String(500))

    # Notifications and communications
    notification_email = Column(String(255))
    notification_sent = Column(Boolean, default=False)
    notification_date = Column(DateTime(timezone=True))

    # Compliance and audit
    compliance_flags = Column(JSON)  # Array of compliance issues
    regulatory_reporting_required = Column(Boolean, default=False)
    suspicious_activity_flag = Column(Boolean, default=False)

    # Performance tracking
    processing_time_minutes = Column(Integer)
    cost_basis = Column(Decimal(10, 2))  # Cost to process this payment

    # Audit and tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    claim = relationship("Claim", back_populates="payments")
    policy = relationship("Policy", back_populates="payments")

    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    approver = relationship("User", foreign_keys=[approved_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Self-referencing relationships for voids/reversals
    original_payment = relationship("Payment", foreign_keys=[original_payment_id], remote_side=[id])
    voided_payment = relationship("Payment", foreign_keys=[voided_payment_id], remote_side=[id])

    def __repr__(self):
        return f"<Payment(id={self.id}, payment_number='{self.payment_number}', amount={self.amount}, status='{self.status}')>"

    def to_dict(self, mask_sensitive: bool = True):
        """Convert payment to dictionary with optional sensitive data masking"""
        from app.core.security import mask_sensitive_data

        data = {
            "id": self.id,
            "payment_number": self.payment_number,
            "external_payment_id": self.external_payment_id,
            "batch_id": self.batch_id,
            "claim_id": self.claim_id,
            "policy_id": self.policy_id,
            "payment_method": self.payment_method,
            "payment_type": self.payment_type,
            "status": self.status,
            "amount": float(self.amount) if self.amount else None,
            "currency": self.currency,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "processed_date": self.processed_date.isoformat() if self.processed_date else None,
            "payee_name": self.payee_name,
            "payee_type": self.payee_type,
            "payee_address": self.payee_address,
            "joint_payees": self.joint_payees,
            "bank_name": self.bank_name,
            "account_type": self.account_type,
            "check_number": self.check_number,
            "reserve_allocations": self.reserve_allocations,
            "is_eroding": self.is_eroding,
            "is_tax_reportable": self.is_tax_reportable,
            "tax_year": self.tax_year,
            "withholding_amount": float(self.withholding_amount) if self.withholding_amount else 0,
            "is_settlement_payment": self.is_settlement_payment,
            "requires_approval": self.requires_approval,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date.isoformat() if self.approval_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Handle sensitive data with masking
        if mask_sensitive:
            data["payee_tax_id"] = mask_sensitive_data(self.payee_tax_id) if self.payee_tax_id else None
            data["routing_number"] = mask_sensitive_data(self.routing_number, visible_chars=4) if self.routing_number else None
            data["account_number"] = mask_sensitive_data(self.account_number, visible_chars=4) if self.account_number else None
            data["card_last_four"] = self.card_last_four
        else:
            data["payee_tax_id"] = self.payee_tax_id
            data["routing_number"] = self.routing_number
            data["account_number"] = self.account_number

        return data

    def validate_data(self):
        """Validate payment data"""
        # Validate payment amount
        if self.amount is not None:
            validate_payment_amount(self.amount)

        # Validate routing number for ACH/Wire
        if self.payment_method in [PaymentMethod.ACH.value, PaymentMethod.WIRE.value]:
            if self.routing_number:
                validate_routing_number(self.routing_number)
            if self.account_number:
                validate_account_number(self.account_number)

        # Validate tax withholding
        if self.withholding_amount and self.amount:
            if abs(self.withholding_amount) > abs(self.amount):
                raise ValueError("Withholding amount cannot exceed payment amount")

    def is_processed(self) -> bool:
        """Check if payment has been processed"""
        return self.status in [
            PaymentStatus.COMPLETED.value,
            PaymentStatus.FAILED.value,
            PaymentStatus.VOIDED.value,
            PaymentStatus.REVERSED.value
        ]

    def can_be_voided(self) -> bool:
        """Check if payment can be voided"""
        return self.status in [
            PaymentStatus.CREATED.value,
            PaymentStatus.PENDING.value,
            PaymentStatus.COMPLETED.value
        ] and not self.voided_payment_id

    def can_be_reversed(self) -> bool:
        """Check if payment can be reversed"""
        return (
            self.status == PaymentStatus.COMPLETED.value and
            self.processed_date and
            (date.today() - self.processed_date).days <= 90  # 90-day reversal window
        )

    def calculate_net_amount(self) -> PyDecimal:
        """Calculate net amount after withholding"""
        net = self.amount or PyDecimal('0')
        withholding = self.withholding_amount or PyDecimal('0')
        return net - withholding

    def add_reserve_allocation(self, reserve_line_type: str, amount: PyDecimal, description: str = None):
        """Add reserve line allocation"""
        if not self.reserve_allocations:
            self.reserve_allocations = []

        allocation = {
            "reserve_line_type": reserve_line_type,
            "amount": float(amount),
            "description": description,
            "created_date": datetime.utcnow().isoformat()
        }

        self.reserve_allocations.append(allocation)

    def get_total_allocated_amount(self) -> PyDecimal:
        """Get total amount allocated across reserve lines"""
        if not self.reserve_allocations:
            return PyDecimal('0')

        total = PyDecimal('0')
        for allocation in self.reserve_allocations:
            total += PyDecimal(str(allocation.get('amount', 0)))

        return total

    def validate_reserve_allocations(self):
        """Validate that reserve allocations don't exceed payment amount"""
        total_allocated = self.get_total_allocated_amount()
        payment_amount = abs(self.amount) if self.amount else PyDecimal('0')

        if total_allocated > payment_amount:
            raise ValueError("Total reserve allocations cannot exceed payment amount")

    def generate_payment_number(self):
        """Generate unique payment number"""
        # Format: PAY-YYYYMMDD-HHMMSS-ID
        timestamp = datetime.utcnow()
        self.payment_number = f"PAY-{timestamp.strftime('%Y%m%d-%H%M%S')}-{self.id or 'TEMP'}"

    def set_payment_details(self, details: dict):
        """Set encrypted payment details"""
        import json
        from app.utils.encryption import encrypt_payment_info

        encrypted_details = encrypt_payment_info(details)
        self.payment_details = json.dumps(encrypted_details)

    def get_payment_details(self) -> dict:
        """Get decrypted payment details"""
        import json
        from app.utils.encryption import decrypt_payment_info

        if not self.payment_details:
            return {}

        try:
            encrypted_details = json.loads(self.payment_details)
            return decrypt_payment_info(encrypted_details)
        except (json.JSONDecodeError, Exception):
            return {}

    def void_payment(self, void_reason: str, voided_by: int):
        """Void the payment"""
        if not self.can_be_voided():
            raise ValueError("Payment cannot be voided in current status")

        self.status = PaymentStatus.VOIDED.value
        self.void_reason = void_reason
        self.updated_by = voided_by
        self.updated_at = func.now()

    def reverse_payment(self, reversal_reason: str, reversed_by: int) -> 'Payment':
        """Create a reversal payment"""
        if not self.can_be_reversed():
            raise ValueError("Payment cannot be reversed")

        # Create reversal payment with negative amount
        reversal = Payment(
            payment_method=self.payment_method,
            payment_type=f"{self.payment_type}_reversal",
            status=PaymentStatus.CREATED.value,
            amount=-self.amount,  # Negative amount for reversal
            currency=self.currency,
            payment_date=date.today(),
            payee_name=self.payee_name,
            payee_type=self.payee_type,
            claim_id=self.claim_id,
            policy_id=self.policy_id,
            original_payment_id=self.id,
            reversal_reason=reversal_reason,
            created_by=reversed_by
        )

        # Copy payment details
        if self.payment_details:
            reversal.payment_details = self.payment_details

        # Copy banking details
        reversal.bank_name = self.bank_name
        reversal.routing_number = self.routing_number
        reversal.account_number = self.account_number
        reversal.account_type = self.account_type

        return reversal

    def requires_supervisor_approval(self) -> bool:
        """Check if payment requires supervisor approval"""
        approval_thresholds = {
            "amount": PyDecimal('10000'),  # $10,000
            "settlement": PyDecimal('5000'),  # $5,000 for settlements
        }

        if abs(self.amount) >= approval_thresholds["amount"]:
            return True

        if self.is_settlement_payment and abs(self.amount) >= approval_thresholds["settlement"]:
            return True

        return False

    def calculate_processing_fee(self) -> PyDecimal:
        """Calculate processing fee based on payment method and amount"""
        fee_schedules = {
            PaymentMethod.ACH.value: PyDecimal('0.25'),  # Flat fee
            PaymentMethod.WIRE.value: PyDecimal('25.00'),  # Flat fee
            PaymentMethod.CARD.value: PyDecimal('0.029'),  # 2.9% of amount
            PaymentMethod.CHECK.value: PyDecimal('2.50'),  # Flat fee
        }

        base_fee = fee_schedules.get(self.payment_method, PyDecimal('0'))

        if self.payment_method == PaymentMethod.CARD.value:
            # Percentage-based fee
            return abs(self.amount) * base_fee
        else:
            # Flat fee
            return base_fee

    def update_processing_fee(self):
        """Update the processing fee"""
        self.processing_fee = self.calculate_processing_fee()

    def is_high_value(self) -> bool:
        """Check if this is a high-value payment requiring special handling"""
        high_value_threshold = PyDecimal('100000')  # $100,000
        return abs(self.amount) >= high_value_threshold

    def get_compliance_flags(self) -> list:
        """Get list of compliance flags for this payment"""
        flags = []

        if self.is_high_value():
            flags.append("high_value")

        if self.amount and abs(self.amount) >= PyDecimal('10000'):
            flags.append("ctf_reporting_required")  # Currency Transaction Report

        if self.payee_type == "foreign_entity":
            flags.append("foreign_payee")

        if self.is_tax_reportable and not self.payee_tax_id:
            flags.append("missing_tax_id")

        return flags