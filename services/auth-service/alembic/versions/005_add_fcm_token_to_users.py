"""add fcm_token to users

Revision ID: 005
Revises: 004
Create Date: 2026-03-14 22:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("fcm_token", sa.String(500), nullable=True))
    op.create_index("idx_users_fcm_token", "users", ["fcm_token"])


def downgrade() -> None:
    op.drop_index("idx_users_fcm_token", table_name="users")
    op.drop_column("users", "fcm_token")
