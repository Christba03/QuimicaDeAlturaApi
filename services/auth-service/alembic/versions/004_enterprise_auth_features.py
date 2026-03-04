"""enterprise_auth_features

Adds all tables and columns introduced by the robustness roadmap:
  - user_sessions: token_family, family_invalidated, GeoIP fields
  - oauth_accounts table
  - api_keys table
  - policies (ABAC) table

Revision ID: 004
Revises: 003
Create Date: 2026-03-04 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # user_sessions — token family + GeoIP columns
    # -----------------------------------------------------------------------
    op.add_column(
        "user_sessions",
        sa.Column(
            "token_family",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.add_column(
        "user_sessions",
        sa.Column("family_invalidated", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("user_sessions", sa.Column("country_code", sa.String(2), nullable=True))
    op.add_column("user_sessions", sa.Column("country_name", sa.String(100), nullable=True))
    op.add_column("user_sessions", sa.Column("region_name", sa.String(100), nullable=True))
    op.add_column("user_sessions", sa.Column("city", sa.String(100), nullable=True))
    op.add_column("user_sessions", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("user_sessions", sa.Column("longitude", sa.Float(), nullable=True))

    op.create_index("idx_sessions_token_family", "user_sessions", ["token_family"])
    op.create_index("idx_sessions_family_invalidated", "user_sessions", ["family_invalidated"])

    # -----------------------------------------------------------------------
    # oauth_accounts
    # -----------------------------------------------------------------------
    op.create_table(
        "oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("provider_email", sa.String(255), nullable=True),
        sa.Column("provider_name", sa.String(255), nullable=True),
        sa.Column("provider_avatar_url", sa.String(500), nullable=True),
        sa.Column("provider_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )
    op.create_index("idx_oauth_user_id", "oauth_accounts", ["user_id"])
    op.create_index("idx_oauth_provider_user_id", "oauth_accounts", ["provider_user_id"])

    # -----------------------------------------------------------------------
    # api_keys
    # -----------------------------------------------------------------------
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("scopes", postgresql.ARRAY(sa.String(100)), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("idx_api_keys_key_hash", "api_keys", ["key_hash"])
    op.create_index("idx_api_keys_is_active", "api_keys", ["is_active"])
    op.create_index("idx_api_keys_expires_at", "api_keys", ["expires_at"])

    # -----------------------------------------------------------------------
    # policies (ABAC)
    # -----------------------------------------------------------------------
    op.create_table(
        "policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject_type", sa.String(50), nullable=False),
        sa.Column("subject_id", sa.String(255), nullable=False),
        sa.Column("resource", sa.String(255), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("effect", sa.String(10), nullable=False, server_default="allow"),
        sa.Column("conditions", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_policies_subject_type", "policies", ["subject_type"])
    op.create_index("idx_policies_subject_id", "policies", ["subject_id"])
    op.create_index("idx_policies_resource", "policies", ["resource"])
    op.create_index("idx_policies_action", "policies", ["action"])
    op.create_index("idx_policies_is_active", "policies", ["is_active"])


def downgrade() -> None:
    # Policies
    op.drop_index("idx_policies_is_active", table_name="policies")
    op.drop_index("idx_policies_action", table_name="policies")
    op.drop_index("idx_policies_resource", table_name="policies")
    op.drop_index("idx_policies_subject_id", table_name="policies")
    op.drop_index("idx_policies_subject_type", table_name="policies")
    op.drop_table("policies")

    # API keys
    op.drop_index("idx_api_keys_expires_at", table_name="api_keys")
    op.drop_index("idx_api_keys_is_active", table_name="api_keys")
    op.drop_index("idx_api_keys_key_hash", table_name="api_keys")
    op.drop_index("idx_api_keys_user_id", table_name="api_keys")
    op.drop_table("api_keys")

    # OAuth accounts
    op.drop_index("idx_oauth_provider_user_id", table_name="oauth_accounts")
    op.drop_index("idx_oauth_user_id", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")

    # user_sessions columns
    op.drop_index("idx_sessions_family_invalidated", table_name="user_sessions")
    op.drop_index("idx_sessions_token_family", table_name="user_sessions")
    op.drop_column("user_sessions", "longitude")
    op.drop_column("user_sessions", "latitude")
    op.drop_column("user_sessions", "city")
    op.drop_column("user_sessions", "region_name")
    op.drop_column("user_sessions", "country_name")
    op.drop_column("user_sessions", "country_code")
    op.drop_column("user_sessions", "family_invalidated")
    op.drop_column("user_sessions", "token_family")
