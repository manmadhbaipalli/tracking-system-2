"""
Claims Service Platform - Payment Service

Payment processing service with reserve allocation, settlement management,
and multiple payment methods.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from enum import Enum

from app.models.payment import Payment, PaymentStatus
from app.models.claim import Claim
from app.models.policy import Policy
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.audit_service import log_action


class PaymentMethodType(Enum):
    """Payment method types"""
    ACH = "ach"
    WIRE = "wire"
    CARD = "card"
    STRIPE = "stripe"
    CHECK = "check"


class PaymentRequest:
    """Payment processing request"""
    def __init__(self, claim_id: int, payment_method: PaymentMethodType, amount: Decimal, **kwargs):
        self.claim_id = claim_id
        self.payment_method = payment_method
        self.amount = amount
        self.recipients = kwargs.get('recipients', [])
        self.reserve_allocations = kwargs.get('reserve_allocations', [])
        self.routing_rules = kwargs.get('routing_rules', {})
        self.tax_reportable = kwargs.get('tax_reportable', False)
        self.documentation = kwargs.get('documentation', [])


class PaymentResult:
    """Payment processing result"""
    def __init__(self, success: bool, payment_id: Optional[int] = None, **kwargs):
        self.success = success
        self.payment_id = payment_id
        self.transaction_id = kwargs.get('transaction_id')
        self.status = kwargs.get('status', 'pending')
        self.message = kwargs.get('message', '')
        self.error_details = kwargs.get('error_details', {})


class ReserveAllocation:
    """Reserve allocation details"""
    def __init__(self, reserve_line: str, amount: Decimal, eroding: bool = True):
        self.reserve_line = reserve_line
        self.amount = amount
        self.eroding = eroding


class AllocationResult:
    """Reserve allocation result"""
    def __init__(self, success: bool, allocations: List[Dict[str, Any]], **kwargs):
        self.success = success
        self.allocations = allocations
        self.total_allocated = kwargs.get('total_allocated', Decimal('0'))
        self.remaining_reserves = kwargs.get('remaining_reserves', {})
        self.validation_errors = kwargs.get('validation_errors', [])


class PaymentRecipient:
    """Payment recipient details"""
    def __init__(self, name: str, payment_method: Dict[str, Any], amount: Decimal, **kwargs):
        self.name = name
        self.payment_method = payment_method
        self.amount = amount
        self.tax_id = kwargs.get('tax_id')
        self.address = kwargs.get('address', {})
        self.is_joint_payee = kwargs.get('is_joint_payee', False)


class PaymentService:
    """Payment processing and reserve management service"""

    def __init__(self, db: Session):
        self.db = db

    async def process_payment(
        self,
        payment_request: PaymentRequest,
        user_id: int
    ) -> PaymentResult:
        """Process payment with multiple methods and reserve allocation"""

        try:
            # Verify claim exists
            claim = self.db.query(Claim).filter(
                Claim.id == payment_request.claim_id,
                Claim.is_deleted == False
            ).first()

            if not claim:
                raise ValueError("Claim not found")

            # Validate reserve allocation
            if payment_request.reserve_allocations:
                allocation_result = await self._validate_reserve_allocation(
                    claim,
                    payment_request.reserve_allocations,
                    payment_request.amount
                )
                if not allocation_result.success:
                    return PaymentResult(
                        success=False,
                        message="Reserve allocation validation failed",
                        error_details={"validation_errors": allocation_result.validation_errors}
                    )

            # Create payment record
            payment_data = {
                "claim_id": payment_request.claim_id,
                "payment_method": payment_request.payment_method.value,
                "amount": payment_request.amount,
                "status": PaymentStatus.PENDING.value,
                "tax_reportable": payment_request.tax_reportable,
                "created_by": user_id,
                "updated_by": user_id
            }

            payment = Payment(**payment_data)

            # Store recipient and allocation details
            payment.metadata = {
                "recipients": [
                    {
                        "name": recipient.name,
                        "payment_method": recipient.payment_method,
                        "amount": float(recipient.amount),
                        "tax_id": recipient.tax_id,
                        "is_joint_payee": recipient.is_joint_payee
                    }
                    for recipient in payment_request.recipients
                ],
                "reserve_allocations": [
                    {
                        "reserve_line": alloc.reserve_line,
                        "amount": float(alloc.amount),
                        "eroding": alloc.eroding
                    }
                    for alloc in payment_request.reserve_allocations
                ],
                "routing_rules": payment_request.routing_rules,
                "documentation": payment_request.documentation
            }

            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)

            # Process payment based on method
            processing_result = await self._process_payment_by_method(
                payment,
                payment_request
            )

            # Update payment status based on processing result
            payment.status = processing_result.get('status', PaymentStatus.PENDING.value)
            if processing_result.get('transaction_id'):
                payment.transaction_id = processing_result['transaction_id']

            # Update reserves if payment is successful
            if processing_result.get('success'):
                await self._update_reserves_for_payment(claim, payment_request.reserve_allocations)

            self.db.commit()

            # Log payment processing
            await log_action(
                self.db,
                user_id,
                "payment_process",
                entity_type="payment",
                entity_id=payment.id,
                details={
                    "claim_id": payment_request.claim_id,
                    "amount": float(payment_request.amount),
                    "payment_method": payment_request.payment_method.value,
                    "processing_result": processing_result
                }
            )

            return PaymentResult(
                success=processing_result.get('success', False),
                payment_id=payment.id,
                transaction_id=processing_result.get('transaction_id'),
                status=payment.status,
                message=processing_result.get('message', 'Payment processed')
            )

        except ValueError as e:
            self.db.rollback()
            return PaymentResult(
                success=False,
                message=str(e)
            )
        except Exception as e:
            self.db.rollback()
            await log_action(
                self.db,
                user_id,
                "payment_process_error",
                entity_type="payment",
                entity_id=None,
                details={
                    "error": str(e),
                    "claim_id": payment_request.claim_id
                }
            )
            raise Exception(f"Payment processing failed: {str(e)}")

    async def allocate_reserves(
        self,
        claim_id: int,
        allocations: List[ReserveAllocation],
        user_id: int
    ) -> AllocationResult:
        """Allocate reserves across multiple reserve lines"""

        try:
            # Verify claim exists
            claim = self.db.query(Claim).filter(
                Claim.id == claim_id,
                Claim.is_deleted == False
            ).first()

            if not claim:
                raise ValueError("Claim not found")

            # Get current reserve amounts
            current_reserves = self._get_claim_reserves(claim)
            validation_errors = []
            total_allocated = Decimal('0')

            # Validate each allocation
            for allocation in allocations:
                current_amount = current_reserves.get(allocation.reserve_line, Decimal('0'))

                if allocation.amount > current_amount:
                    validation_errors.append(
                        f"Insufficient reserves in {allocation.reserve_line}: "
                        f"requested ${allocation.amount}, available ${current_amount}"
                    )
                else:
                    total_allocated += allocation.amount

            # Return validation errors if any
            if validation_errors:
                return AllocationResult(
                    success=False,
                    allocations=[],
                    validation_errors=validation_errors
                )

            # Apply allocations
            updated_reserves = current_reserves.copy()
            allocation_details = []

            for allocation in allocations:
                if allocation.eroding:
                    updated_reserves[allocation.reserve_line] -= allocation.amount

                allocation_details.append({
                    "reserve_line": allocation.reserve_line,
                    "allocated_amount": float(allocation.amount),
                    "eroding": allocation.eroding,
                    "remaining_reserve": float(updated_reserves[allocation.reserve_line])
                })

            # Update claim reserves
            await self._update_claim_reserves(claim, updated_reserves)

            # Log allocation
            await log_action(
                self.db,
                user_id,
                "reserve_allocate",
                entity_type="claim",
                entity_id=claim_id,
                details={
                    "total_allocated": float(total_allocated),
                    "allocations": allocation_details
                }
            )

            return AllocationResult(
                success=True,
                allocations=allocation_details,
                total_allocated=total_allocated,
                remaining_reserves=updated_reserves
            )

        except ValueError as e:
            raise e
        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "reserve_allocate_error",
                entity_type="claim",
                entity_id=claim_id,
                details={"error": str(e)}
            )
            raise Exception(f"Reserve allocation failed: {str(e)}")

    async def calculate_settlement_amount(
        self,
        claim_id: int,
        percentage: float,
        user_id: int
    ) -> Decimal:
        """Calculate settlement amount based on percentage of reserves"""

        try:
            claim = self.db.query(Claim).filter(
                Claim.id == claim_id,
                Claim.is_deleted == False
            ).first()

            if not claim:
                raise ValueError("Claim not found")

            # Get total reserves
            total_reserves = getattr(claim, 'total_reserve', Decimal('0'))

            # Calculate settlement amount
            settlement_amount = total_reserves * (Decimal(str(percentage)) / 100)

            # Log calculation
            await log_action(
                self.db,
                user_id,
                "settlement_calculate",
                entity_type="claim",
                entity_id=claim_id,
                details={
                    "total_reserves": float(total_reserves),
                    "percentage": percentage,
                    "settlement_amount": float(settlement_amount)
                }
            )

            return settlement_amount

        except ValueError as e:
            raise e
        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "settlement_calculate_error",
                entity_type="claim",
                entity_id=claim_id,
                details={"error": str(e)}
            )
            raise Exception(f"Settlement calculation failed: {str(e)}")

    async def validate_payment_method(
        self,
        method: PaymentMethodType,
        details: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Validate payment method details"""

        try:
            validation_errors = []
            warnings = []

            if method == PaymentMethodType.ACH:
                # Validate ACH details
                required_fields = ['routing_number', 'account_number', 'account_type']
                for field in required_fields:
                    if not details.get(field):
                        validation_errors.append(f"ACH {field} is required")

                if details.get('routing_number') and len(details['routing_number']) != 9:
                    validation_errors.append("ACH routing number must be 9 digits")

            elif method == PaymentMethodType.WIRE:
                # Validate wire transfer details
                required_fields = ['bank_name', 'routing_number', 'account_number', 'swift_code']
                for field in required_fields:
                    if not details.get(field):
                        validation_errors.append(f"Wire {field} is required")

            elif method == PaymentMethodType.CARD:
                # Validate card details
                required_fields = ['card_number', 'expiry_date', 'cvv']
                for field in required_fields:
                    if not details.get(field):
                        validation_errors.append(f"Card {field} is required")

                # Additional card validations would go here
                if details.get('card_number') and len(details['card_number'].replace(' ', '')) < 13:
                    validation_errors.append("Invalid card number")

            elif method == PaymentMethodType.STRIPE:
                # Validate Stripe payment details
                if not details.get('stripe_customer_id') and not details.get('stripe_payment_method_id'):
                    validation_errors.append("Stripe customer ID or payment method ID is required")

            # Business rule warnings
            if method in [PaymentMethodType.WIRE, PaymentMethodType.ACH]:
                if not details.get('recipient_name'):
                    warnings.append("Recipient name is recommended for bank transfers")

            # Log validation
            await log_action(
                self.db,
                user_id,
                "payment_method_validate",
                entity_type="payment",
                entity_id=None,
                details={
                    "payment_method": method.value,
                    "errors_count": len(validation_errors),
                    "warnings_count": len(warnings)
                }
            )

            return {
                "is_valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "warnings": warnings,
                "payment_method": method.value
            }

        except Exception as e:
            await log_action(
                self.db,
                user_id,
                "payment_method_validate_error",
                entity_type="payment",
                entity_id=None,
                details={"error": str(e)}
            )
            raise Exception(f"Payment method validation failed: {str(e)}")

    async def _validate_reserve_allocation(
        self,
        claim: Claim,
        allocations: List[ReserveAllocation],
        payment_amount: Decimal
    ) -> AllocationResult:
        """Validate reserve allocation against available reserves"""

        current_reserves = self._get_claim_reserves(claim)
        validation_errors = []
        total_allocated = Decimal('0')

        for allocation in allocations:
            total_allocated += allocation.amount
            current_amount = current_reserves.get(allocation.reserve_line, Decimal('0'))

            if allocation.amount > current_amount:
                validation_errors.append(
                    f"Insufficient reserves in {allocation.reserve_line}: "
                    f"requested ${allocation.amount}, available ${current_amount}"
                )

        # Check if total allocation matches payment amount
        if total_allocated != payment_amount:
            validation_errors.append(
                f"Total allocation ${total_allocated} does not match payment amount ${payment_amount}"
            )

        return AllocationResult(
            success=len(validation_errors) == 0,
            allocations=[],
            validation_errors=validation_errors
        )

    def _get_claim_reserves(self, claim: Claim) -> Dict[str, Decimal]:
        """Get current reserve amounts by line"""

        # Default reserve structure - in production, this would come from the claim data
        reserves = {
            "indemnity": getattr(claim, 'indemnity_reserve', Decimal('0')),
            "expense": getattr(claim, 'expense_reserve', Decimal('0')),
            "medical": getattr(claim, 'medical_reserve', Decimal('0')),
            "legal": getattr(claim, 'legal_reserve', Decimal('0'))
        }

        # If claim has reserve_allocations JSON field, use that
        if hasattr(claim, 'reserve_allocations') and claim.reserve_allocations:
            for line, amount in claim.reserve_allocations.items():
                reserves[line] = Decimal(str(amount))

        return reserves

    async def _update_claim_reserves(self, claim: Claim, updated_reserves: Dict[str, Decimal]):
        """Update claim reserve amounts"""

        # Update individual reserve fields if they exist
        for line, amount in updated_reserves.items():
            field_name = f"{line}_reserve"
            if hasattr(claim, field_name):
                setattr(claim, field_name, amount)

        # Also update reserve_allocations JSON field if it exists
        if hasattr(claim, 'reserve_allocations'):
            claim.reserve_allocations = {
                line: float(amount) for line, amount in updated_reserves.items()
            }

        self.db.commit()

    async def _update_reserves_for_payment(self, claim: Claim, allocations: List[ReserveAllocation]):
        """Update reserves after successful payment"""

        current_reserves = self._get_claim_reserves(claim)

        for allocation in allocations:
            if allocation.eroding:
                current_reserves[allocation.reserve_line] -= allocation.amount

        await self._update_claim_reserves(claim, current_reserves)

    async def _process_payment_by_method(
        self,
        payment: Payment,
        payment_request: PaymentRequest
    ) -> Dict[str, Any]:
        """Process payment based on method type"""

        try:
            method = payment_request.payment_method

            if method == PaymentMethodType.ACH:
                return await self._process_ach_payment(payment, payment_request)
            elif method == PaymentMethodType.WIRE:
                return await self._process_wire_payment(payment, payment_request)
            elif method == PaymentMethodType.CARD:
                return await self._process_card_payment(payment, payment_request)
            elif method == PaymentMethodType.STRIPE:
                return await self._process_stripe_payment(payment, payment_request)
            elif method == PaymentMethodType.CHECK:
                return await self._process_check_payment(payment, payment_request)
            else:
                return {
                    "success": False,
                    "message": f"Unsupported payment method: {method.value}"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Payment processing error: {str(e)}"
            }

    async def _process_ach_payment(self, payment: Payment, request: PaymentRequest) -> Dict[str, Any]:
        """Process ACH payment - placeholder implementation"""
        # In production, integrate with actual ACH processor
        return {
            "success": True,
            "status": PaymentStatus.PENDING.value,
            "transaction_id": f"ACH_{payment.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "message": "ACH payment initiated"
        }

    async def _process_wire_payment(self, payment: Payment, request: PaymentRequest) -> Dict[str, Any]:
        """Process wire transfer - placeholder implementation"""
        # In production, integrate with banking API
        return {
            "success": True,
            "status": PaymentStatus.PROCESSING.value,
            "transaction_id": f"WIRE_{payment.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "message": "Wire transfer initiated"
        }

    async def _process_card_payment(self, payment: Payment, request: PaymentRequest) -> Dict[str, Any]:
        """Process card payment - placeholder implementation"""
        # In production, integrate with card processor
        return {
            "success": True,
            "status": PaymentStatus.COMPLETED.value,
            "transaction_id": f"CARD_{payment.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "message": "Card payment completed"
        }

    async def _process_stripe_payment(self, payment: Payment, request: PaymentRequest) -> Dict[str, Any]:
        """Process Stripe payment - placeholder implementation"""
        # In production, integrate with Stripe API
        return {
            "success": True,
            "status": PaymentStatus.COMPLETED.value,
            "transaction_id": f"STRIPE_{payment.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "message": "Stripe payment completed"
        }

    async def _process_check_payment(self, payment: Payment, request: PaymentRequest) -> Dict[str, Any]:
        """Process check payment - placeholder implementation"""
        return {
            "success": True,
            "status": PaymentStatus.PENDING.value,
            "transaction_id": f"CHECK_{payment.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "message": "Check payment prepared for mailing"
        }