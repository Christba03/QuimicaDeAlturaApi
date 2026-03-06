"""
Idempotent DB bootstrap: creates tables that Alembic migrations 001-004 would
create, then stamps alembic_version at 004 so future migrations work normally.

Runs with asyncpg (already installed) so no extra dependencies are needed.
"""

import asyncio
import os
import re


async def main():
    import asyncpg

    db_url = os.environ.get("DATABASE_URL", "")
    m = re.match(
        r"postgresql\+asyncpg://(?P<user>[^:]+):(?P<pw>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<db>.+)",
        db_url,
    )
    if not m:
        print(f"Cannot parse DATABASE_URL ({db_url!r}), skipping bootstrap.")
        return

    conn = await asyncpg.connect(
        user=m.group("user"),
        password=m.group("pw"),
        host=m.group("host"),
        port=int(m.group("port")),
        database=m.group("db"),
    )

    try:
        tables = [
            r["tablename"]
            for r in await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )
        ]
        print(f"Existing tables: {tables}")

        # -- verification_codes --
        if "verification_codes" not in tables:
            print("Creating verification_codes...")
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE verificationcodetype AS ENUM (
                        'EMAIL_VERIFICATION', 'PASSWORD_RESET', 'TWO_FACTOR_EMAIL'
                    );
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            await conn.execute("""
                CREATE TABLE verification_codes (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    code_hash VARCHAR(255) NOT NULL,
                    code_type verificationcodetype NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    used_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_verification_codes_user_id ON verification_codes(user_id);
                CREATE INDEX IF NOT EXISTS ix_verification_codes_code_type ON verification_codes(code_type);
                CREATE INDEX IF NOT EXISTS ix_verification_codes_expires_at ON verification_codes(expires_at);
            """)

        # -- two_factor_backup_codes --
        if "two_factor_backup_codes" not in tables:
            print("Creating two_factor_backup_codes...")
            await conn.execute("""
                CREATE TABLE two_factor_backup_codes (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    code_hash VARCHAR(255) NOT NULL UNIQUE,
                    used_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_two_factor_backup_codes_user_id ON two_factor_backup_codes(user_id);
            """)

        # -- security_events --
        if "security_events" not in tables:
            print("Creating security_events...")
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE securityeventtype AS ENUM (
                        'LOGIN_SUCCESS','LOGIN_FAILED','LOGOUT','PASSWORD_CHANGED',
                        'PASSWORD_RESET_REQUESTED','PASSWORD_RESET_COMPLETED','EMAIL_VERIFIED',
                        'TWO_FACTOR_ENABLED','TWO_FACTOR_DISABLED','TWO_FACTOR_VERIFIED',
                        'TWO_FACTOR_FAILED','ACCOUNT_LOCKED','ACCOUNT_UNLOCKED',
                        'SESSION_REVOKED','SUSPICIOUS_ACTIVITY'
                    );
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """)
            await conn.execute("""
                CREATE TABLE security_events (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    event_type securityeventtype NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_security_events_user_id ON security_events(user_id);
                CREATE INDEX IF NOT EXISTS ix_security_events_event_type ON security_events(event_type);
                CREATE INDEX IF NOT EXISTS ix_security_events_created_at ON security_events(created_at);
            """)

        # -- oauth_accounts (matches OAuthAccount model) --
        if "oauth_accounts" not in tables:
            print("Creating oauth_accounts...")
            await conn.execute("""
                CREATE TABLE oauth_accounts (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    provider VARCHAR(50) NOT NULL,
                    provider_user_id VARCHAR(255) NOT NULL,
                    provider_email VARCHAR(255),
                    provider_name VARCHAR(255),
                    provider_avatar_url VARCHAR(500),
                    provider_data JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    CONSTRAINT uq_oauth_provider_user UNIQUE(provider, provider_user_id)
                );
                CREATE INDEX IF NOT EXISTS ix_oauth_accounts_user_id ON oauth_accounts(user_id);
                CREATE INDEX IF NOT EXISTS ix_oauth_accounts_provider_user_id ON oauth_accounts(provider_user_id);
            """)

        # -- api_keys (matches APIKey model — scopes is text[] not JSONB) --
        if "api_keys" not in tables:
            print("Creating api_keys...")
            await conn.execute("""
                CREATE TABLE api_keys (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    key_prefix VARCHAR(12) NOT NULL,
                    key_hash VARCHAR(64) NOT NULL UNIQUE,
                    scopes VARCHAR(100)[] NOT NULL DEFAULT '{}',
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    last_used_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys(user_id);
                CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys(key_hash);
                CREATE INDEX IF NOT EXISTS ix_api_keys_is_active ON api_keys(is_active);
                CREATE INDEX IF NOT EXISTS ix_api_keys_expires_at ON api_keys(expires_at);
            """)

        # -- policies (matches Policy model — ABAC with subject_type/subject_id) --
        if "policies" not in tables:
            print("Creating policies...")
            await conn.execute("""
                CREATE TABLE policies (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    subject_type VARCHAR(50) NOT NULL,
                    subject_id VARCHAR(255) NOT NULL,
                    resource VARCHAR(255) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    effect VARCHAR(10) NOT NULL DEFAULT 'allow',
                    conditions JSONB,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_policies_subject_type ON policies(subject_type);
                CREATE INDEX IF NOT EXISTS ix_policies_subject_id ON policies(subject_id);
                CREATE INDEX IF NOT EXISTS ix_policies_resource ON policies(resource);
                CREATE INDEX IF NOT EXISTS ix_policies_action ON policies(action);
                CREATE INDEX IF NOT EXISTS ix_policies_is_active ON policies(is_active);
            """)

        # -- Add missing columns to user_sessions (matches UserSession model) --
        session_cols = [
            r["column_name"]
            for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'user_sessions'"
            )
        ]
        new_session_cols = [
            ("token_family", "UUID DEFAULT uuid_generate_v4() NOT NULL"),
            ("family_invalidated", "BOOLEAN DEFAULT FALSE NOT NULL"),
            ("device_fingerprint", "VARCHAR(64)"),
            ("device_name", "VARCHAR(100)"),
            ("device_type", "VARCHAR(50)"),
            ("country_code", "VARCHAR(2)"),
            ("country_name", "VARCHAR(100)"),
            ("region_name", "VARCHAR(100)"),
            ("city", "VARCHAR(100)"),
            ("latitude", "DOUBLE PRECISION"),
            ("longitude", "DOUBLE PRECISION"),
            ("is_trusted", "BOOLEAN DEFAULT FALSE NOT NULL"),
            ("trusted_until", "TIMESTAMP WITH TIME ZONE"),
        ]
        for col_name, col_type in new_session_cols:
            if col_name not in session_cols:
                print(f"  Adding user_sessions.{col_name}")
                await conn.execute(f"ALTER TABLE user_sessions ADD COLUMN {col_name} {col_type}")

        # -- password_history on users (migration 002) --
        user_cols = [
            r["column_name"]
            for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
            )
        ]
        if "password_history" not in user_cols:
            print("  Adding users.password_history")
            await conn.execute("ALTER TABLE users ADD COLUMN password_history JSONB NOT NULL DEFAULT '[]'")

        # -- Stamp alembic at head (004) --
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            )
        """)
        await conn.execute("DELETE FROM alembic_version")
        await conn.execute("INSERT INTO alembic_version (version_num) VALUES ('004')")

        print("DB bootstrap complete. Alembic stamped at 004.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
