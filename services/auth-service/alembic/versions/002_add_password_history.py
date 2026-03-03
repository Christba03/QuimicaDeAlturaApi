"""add_password_history

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_history column to users table
    op.add_column('users', sa.Column('password_history', postgresql.JSONB(), nullable=False, server_default='[]'))
    
    # Create GIN index for efficient JSONB queries
    op.create_index('idx_users_password_history', 'users', ['password_history'], postgresql_using='gin')


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_users_password_history', table_name='users')
    
    # Drop column
    op.drop_column('users', 'password_history')
