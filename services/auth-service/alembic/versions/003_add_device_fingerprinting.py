"""add_device_fingerprinting

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add device fingerprinting columns to user_sessions table
    op.add_column('user_sessions', sa.Column('device_fingerprint', sa.String(64), nullable=True))
    op.add_column('user_sessions', sa.Column('device_name', sa.String(100), nullable=True))
    op.add_column('user_sessions', sa.Column('device_type', sa.String(50), nullable=True))
    op.add_column('user_sessions', sa.Column('is_trusted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_sessions', sa.Column('trusted_until', sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes
    op.create_index('idx_sessions_device_fingerprint', 'user_sessions', ['device_fingerprint'])
    op.create_index('idx_sessions_is_trusted', 'user_sessions', ['is_trusted'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_sessions_is_trusted', table_name='user_sessions')
    op.drop_index('idx_sessions_device_fingerprint', table_name='user_sessions')
    
    # Drop columns
    op.drop_column('user_sessions', 'trusted_until')
    op.drop_column('user_sessions', 'is_trusted')
    op.drop_column('user_sessions', 'device_type')
    op.drop_column('user_sessions', 'device_name')
    op.drop_column('user_sessions', 'device_fingerprint')
