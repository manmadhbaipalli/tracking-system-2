"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-02-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, DateTime, Date, Numeric, JSON, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.types import TypeDecorator, CHAR
import uuid

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID())
        else:
            return dialect.type_descriptor(CHAR(36))


def upgrade() -> None:
    """Create all tables with proper indexes for performance optimization."""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('email', String(255), nullable=False),
        sa.Column('hashed_password', String(255), nullable=False),
        sa.Column('first_name', String(100), nullable=False),
        sa.Column('last_name', String(100), nullable=False),
        sa.Column('is_active', Boolean, nullable=False, default=True),
        sa.Column('is_superuser', Boolean, nullable=False, default=False),
        sa.Column('role', String(50), nullable=False, default='agent'),
        sa.Column('employee_id', String(50), nullable=True),
        sa.Column('department', String(100), nullable=True),
        sa.Column('last_login', DateTime, nullable=True),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, default=0),
        sa.Column('locked_until', DateTime, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('employee_id')
    )

    # Create indexes for users table
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])

    # Create user_roles table
    op.create_table(
        'user_roles',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', String(50), nullable=False),
        sa.Column('description', String(255), nullable=True),
        sa.Column('permissions', JSON, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create indexes for user_roles
    op.create_index('ix_user_roles_id', 'user_roles', ['id'])
    op.create_index('ix_user_roles_name', 'user_roles', ['name'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('user_id', GUID(), nullable=True),
        sa.Column('action', String(50), nullable=False),
        sa.Column('entity_type', String(50), nullable=False),
        sa.Column('entity_id', GUID(), nullable=False),
        sa.Column('old_values', JSON, nullable=True),
        sa.Column('new_values', JSON, nullable=True),
        sa.Column('changes', JSON, nullable=True),
        sa.Column('ip_address', String(45), nullable=True),
        sa.Column('user_agent', Text, nullable=True),
        sa.Column('session_id', String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )

    # Create indexes for audit_logs
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # Create policies table
    op.create_table(
        'policies',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('policy_number', String(50), nullable=False),
        sa.Column('policy_type', String(50), nullable=False),
        sa.Column('policy_status', String(20), nullable=False, default='ACTIVE'),
        sa.Column('effective_date', Date, nullable=False),
        sa.Column('expiration_date', Date, nullable=False),
        sa.Column('insured_first_name', String(100), nullable=False),
        sa.Column('insured_last_name', String(100), nullable=False),
        sa.Column('organizational_name', String(200), nullable=True),
        sa.Column('ssn_tin_encrypted', String(255), nullable=True),
        sa.Column('ssn_tin_hash', String(64), nullable=True),
        sa.Column('policy_address', String(255), nullable=True),
        sa.Column('policy_city', String(100), nullable=False),
        sa.Column('policy_state', String(2), nullable=False),
        sa.Column('policy_zip', String(10), nullable=False),
        sa.Column('vehicle_details', JSON, nullable=True),
        sa.Column('coverage_details', JSON, nullable=True),
        sa.Column('premium_amount', Numeric(10, 2), nullable=True),
        sa.Column('deductible_amount', Numeric(10, 2), nullable=True),
        sa.Column('agent_id', String(50), nullable=True),
        sa.Column('underwriter', String(100), nullable=True),
        sa.Column('notes', Text, nullable=True),
        sa.Column('loss_date', Date, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('policy_number')
    )

    # Create performance indexes for policies (from design)
    op.create_index('ix_policies_id', 'policies', ['id'])
    op.create_index('ix_policies_policy_number', 'policies', ['policy_number'])
    op.create_index('ix_policies_policy_type', 'policies', ['policy_type'])
    op.create_index('ix_policies_insured_first_name', 'policies', ['insured_first_name'])
    op.create_index('ix_policies_insured_last_name', 'policies', ['insured_last_name'])
    op.create_index('ix_policies_organizational_name', 'policies', ['organizational_name'])
    op.create_index('ix_policies_ssn_tin_hash', 'policies', ['ssn_tin_hash'])
    op.create_index('ix_policies_policy_city', 'policies', ['policy_city'])
    op.create_index('ix_policies_policy_state', 'policies', ['policy_state'])
    op.create_index('ix_policies_policy_zip', 'policies', ['policy_zip'])
    op.create_index('ix_policies_loss_date', 'policies', ['loss_date'])

    # Composite indexes for search performance optimization (from design)
    op.create_index('idx_policy_number_type', 'policies', ['policy_number', 'policy_type'])
    op.create_index('idx_insured_name', 'policies', ['insured_last_name', 'insured_first_name'])
    op.create_index('idx_policy_location', 'policies', ['policy_state', 'policy_city', 'policy_zip'])
    op.create_index('idx_policy_dates', 'policies', ['effective_date', 'expiration_date'])
    op.create_index('idx_policy_status_type', 'policies', ['policy_status', 'policy_type'])
    op.create_index('idx_policy_search_combo', 'policies', ['policy_state', 'policy_type', 'policy_status'])

    # Create claims table
    op.create_table(
        'claims',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('claim_number', String(50), nullable=False),
        sa.Column('policy_id', GUID(), nullable=False),
        sa.Column('date_of_loss', Date, nullable=False),
        sa.Column('claim_status', String(20), nullable=False, default='OPEN'),
        sa.Column('loss_description', Text, nullable=True),
        sa.Column('loss_location', String(255), nullable=True),
        sa.Column('reported_date', Date, nullable=False),
        sa.Column('adjuster_id', GUID(), nullable=True),
        sa.Column('claim_type', String(50), nullable=False),
        sa.Column('coverage_type', String(50), nullable=True),
        sa.Column('reserve_amount', Numeric(12, 2), nullable=True),
        sa.Column('paid_amount', Numeric(12, 2), nullable=False, default=0),
        sa.Column('deductible_amount', Numeric(10, 2), nullable=True),
        sa.Column('claim_level_policy_data', JSON, nullable=True),
        sa.Column('subrogation_referral', Boolean, nullable=False, default=False),
        sa.Column('subrogation_details', JSON, nullable=True),
        sa.Column('injury_incident_details', JSON, nullable=True),
        sa.Column('coding_information', JSON, nullable=True),
        sa.Column('carrier_involvement', JSON, nullable=True),
        sa.Column('scheduled_payments', JSON, nullable=True),
        sa.Column('settlement_details', JSON, nullable=True),
        sa.Column('litigation_status', String(50), nullable=True),
        sa.Column('catastrophe_id', String(50), nullable=True),
        sa.Column('notes', Text, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_number'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['adjuster_id'], ['users.id'], ondelete='SET NULL')
    )

    # Create indexes for claims
    op.create_index('ix_claims_id', 'claims', ['id'])
    op.create_index('ix_claims_claim_number', 'claims', ['claim_number'])
    op.create_index('ix_claims_policy_id', 'claims', ['policy_id'])
    op.create_index('ix_claims_date_of_loss', 'claims', ['date_of_loss'])
    op.create_index('ix_claims_claim_status', 'claims', ['claim_status'])
    op.create_index('ix_claims_adjuster_id', 'claims', ['adjuster_id'])
    op.create_index('ix_claims_claim_type', 'claims', ['claim_type'])
    op.create_index('ix_claims_reported_date', 'claims', ['reported_date'])

    # Composite indexes for claims performance
    op.create_index('idx_claim_policy_status', 'claims', ['policy_id', 'claim_status'])
    op.create_index('idx_claim_date_status', 'claims', ['date_of_loss', 'claim_status'])

    # Create payees table
    op.create_table(
        'payees',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', String(200), nullable=False),
        sa.Column('payee_type', String(50), nullable=False),
        sa.Column('contact_info', JSON, nullable=True),
        sa.Column('payment_methods', JSON, nullable=True),
        sa.Column('tax_id_encrypted', String(255), nullable=True),
        sa.Column('tax_id_hash', String(64), nullable=True),
        sa.Column('kyc_status', String(20), nullable=False, default='PENDING'),
        sa.Column('kyc_verified_at', DateTime, nullable=True),
        sa.Column('kyc_documents', JSON, nullable=True),
        sa.Column('banking_details_encrypted', Text, nullable=True),
        sa.Column('stripe_account_id', String(100), nullable=True),
        sa.Column('is_active', Boolean, nullable=False, default=True),
        sa.Column('vendor_status', String(20), nullable=True),
        sa.Column('notes', Text, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for payees
    op.create_index('ix_payees_id', 'payees', ['id'])
    op.create_index('ix_payees_name', 'payees', ['name'])
    op.create_index('ix_payees_payee_type', 'payees', ['payee_type'])
    op.create_index('ix_payees_tax_id_hash', 'payees', ['tax_id_hash'])
    op.create_index('ix_payees_kyc_status', 'payees', ['kyc_status'])
    op.create_index('ix_payees_is_active', 'payees', ['is_active'])
    op.create_index('ix_payees_stripe_account_id', 'payees', ['stripe_account_id'])

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('payment_number', String(50), nullable=False),
        sa.Column('claim_id', GUID(), nullable=False),
        sa.Column('policy_id', GUID(), nullable=False),
        sa.Column('payment_type', String(50), nullable=False),
        sa.Column('payment_method', String(50), nullable=False),
        sa.Column('payment_status', String(20), nullable=False, default='CREATED'),
        sa.Column('amount', Numeric(12, 2), nullable=False),
        sa.Column('currency', String(3), nullable=False, default='USD'),
        sa.Column('payment_date', Date, nullable=True),
        sa.Column('scheduled_date', Date, nullable=True),
        sa.Column('processed_date', DateTime, nullable=True),
        sa.Column('void_date', DateTime, nullable=True),
        sa.Column('void_reason', Text, nullable=True),
        sa.Column('reversal_date', DateTime, nullable=True),
        sa.Column('reversal_reason', Text, nullable=True),
        sa.Column('reissue_date', DateTime, nullable=True),
        sa.Column('reissue_reason', Text, nullable=True),
        sa.Column('original_payment_id', GUID(), nullable=True),
        sa.Column('reference_number', String(100), nullable=True),
        sa.Column('transaction_id', String(100), nullable=True),
        sa.Column('reserve_lines', JSON, nullable=True),
        sa.Column('tax_withholding_amount', Numeric(10, 2), nullable=True),
        sa.Column('tax_reportable', Boolean, nullable=False, default=False),
        sa.Column('remittance_details', JSON, nullable=True),
        sa.Column('external_payment_id', String(100), nullable=True),
        sa.Column('payment_processor_response', JSON, nullable=True),
        sa.Column('compliance_checks', JSON, nullable=True),
        sa.Column('document_attachments', JSON, nullable=True),
        sa.Column('notes', Text, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_number'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['original_payment_id'], ['payments.id'], ondelete='SET NULL')
    )

    # Create indexes for payments
    op.create_index('ix_payments_id', 'payments', ['id'])
    op.create_index('ix_payments_payment_number', 'payments', ['payment_number'])
    op.create_index('ix_payments_claim_id', 'payments', ['claim_id'])
    op.create_index('ix_payments_policy_id', 'payments', ['policy_id'])
    op.create_index('ix_payments_payment_status', 'payments', ['payment_status'])
    op.create_index('ix_payments_payment_method', 'payments', ['payment_method'])
    op.create_index('ix_payments_payment_date', 'payments', ['payment_date'])
    op.create_index('ix_payments_processed_date', 'payments', ['processed_date'])
    op.create_index('ix_payments_external_payment_id', 'payments', ['external_payment_id'])
    op.create_index('ix_payments_transaction_id', 'payments', ['transaction_id'])

    # Composite indexes for payments performance
    op.create_index('idx_payment_claim_status', 'payments', ['claim_id', 'payment_status'])
    op.create_index('idx_payment_policy_status', 'payments', ['policy_id', 'payment_status'])
    op.create_index('idx_payment_date_status', 'payments', ['payment_date', 'payment_status'])

    # Create payment_payees junction table
    op.create_table(
        'payment_payees',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('payment_id', GUID(), nullable=False),
        sa.Column('payee_id', GUID(), nullable=False),
        sa.Column('amount', Numeric(12, 2), nullable=False),
        sa.Column('percentage', Numeric(5, 2), nullable=True),
        sa.Column('reserve_line_id', String(50), nullable=True),
        sa.Column('erosion_type', String(20), nullable=False, default='eroding'),
        sa.Column('tax_withholding', Numeric(10, 2), nullable=True),
        sa.Column('tax_reportable', Boolean, nullable=False, default=False),
        sa.Column('payment_portion_type', String(50), nullable=True),
        sa.Column('notes', Text, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payee_id'], ['payees.id'], ondelete='CASCADE')
    )

    # Create indexes for payment_payees
    op.create_index('ix_payment_payees_id', 'payment_payees', ['id'])
    op.create_index('ix_payment_payees_payment_id', 'payment_payees', ['payment_id'])
    op.create_index('ix_payment_payees_payee_id', 'payment_payees', ['payee_id'])
    op.create_index('ix_payment_payees_reserve_line_id', 'payment_payees', ['reserve_line_id'])


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table('payment_payees')
    op.drop_table('payments')
    op.drop_table('payees')
    op.drop_table('claims')
    op.drop_table('policies')
    op.drop_table('audit_logs')
    op.drop_table('user_roles')
    op.drop_table('users')