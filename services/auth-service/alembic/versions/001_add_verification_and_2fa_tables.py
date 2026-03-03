"""add_verification_and_2fa_tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create verification_codes table
    op.create_table(
        'verification_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code_hash', sa.String(255), nullable=False),
        sa.Column('code_type', sa.Enum('EMAIL_VERIFICATION', 'PASSWORD_RESET', 'TWO_FACTOR_EMAIL', name='verificationcodetype'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_verification_codes_user_id', 'verification_codes', ['user_id'])
    op.create_index('ix_verification_codes_code_type', 'verification_codes', ['code_type'])
    op.create_index('ix_verification_codes_expires_at', 'verification_codes', ['expires_at'])

    # Create two_factor_backup_codes table
    op.create_table(
        'two_factor_backup_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_two_factor_backup_codes_user_id', 'two_factor_backup_codes', ['user_id'])
    op.create_index('ix_two_factor_backup_codes_code_hash', 'two_factor_backup_codes', ['code_hash'], unique=True)

    # Create security_events table
    op.create_table(
        'security_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.Enum(
            'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'PASSWORD_CHANGED',
            'PASSWORD_RESET_REQUESTED', 'PASSWORD_RESET_COMPLETED', 'EMAIL_VERIFIED',
            'TWO_FACTOR_ENABLED', 'TWO_FACTOR_DISABLED', 'TWO_FACTOR_VERIFIED',
            'TWO_FACTOR_FAILED', 'ACCOUNT_LOCKED', 'ACCOUNT_UNLOCKED',
            'SESSION_REVOKED', 'SUSPICIOUS_ACTIVITY', name='securityeventtype'
        ), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_security_events_user_id', 'security_events', ['user_id'])
    op.create_index('ix_security_events_event_type', 'security_events', ['event_type'])
    op.create_index('ix_security_events_created_at', 'security_events', ['created_at'])

    # Add missing columns to users table if they don't exist
    # Note: These might already exist in the schema, but we'll add them safely
    try:
        op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column('users', sa.Column('email_verification_token', sa.String(255), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('users', sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), nullable=False, server_default='false'))
    except Exception:
        pass

    try:
        op.add_column('users', sa.Column('two_factor_secret', sa.String(255), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('users', sa.Column('last_login_ip', sa.String(45), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    except Exception:
        pass

    try:
        op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_security_events_created_at', table_name='security_events')
    op.drop_index('ix_security_events_event_type', table_name='security_events')
    op.drop_index('ix_security_events_user_id', table_name='security_events')
    op.drop_index('ix_two_factor_backup_codes_code_hash', table_name='two_factor_backup_codes')
    op.drop_index('ix_two_factor_backup_codes_user_id', table_name='two_factor_backup_codes')
    op.drop_index('ix_verification_codes_expires_at', table_name='verification_codes')
    op.drop_index('ix_verification_codes_code_type', table_name='verification_codes')
    op.drop_index('ix_verification_codes_user_id', table_name='verification_codes')

    # Drop tables
    op.drop_table('security_events')
    op.drop_table('two_factor_backup_codes')
    op.drop_table('verification_codes')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS securityeventtype')
    op.execute('DROP TYPE IF EXISTS verificationcodetype')

    # Remove columns from users (if they were added by this migration)
    # Note: In production, you'd want to be more careful about this
    try:
        op.drop_column('users', 'locked_until')
    except Exception:
        pass
    try:
        op.drop_column('users', 'failed_login_attempts')
    except Exception:
        pass
    try:
        op.drop_column('users', 'last_login_ip')
    except Exception:
        pass
    try:
        op.drop_column('users', 'last_login_at')
    except Exception:
        pass
    try:
        op.drop_column('users', 'two_factor_secret')
    except Exception:
        pass
    try:
        op.drop_column('users', 'two_factor_enabled')
    except Exception:
        pass
    try:
        op.drop_column('users', 'email_verified_at')
    except Exception:
        pass
    try:
        op.drop_column('users', 'email_verification_token')
    except Exception:
        pass
    try:
        op.drop_column('users', 'email_verified')
    except Exception:
        pass
