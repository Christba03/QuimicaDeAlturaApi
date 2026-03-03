-- Migration: Update user_sessions table to match implementation
-- Run this if you have an existing database with the old schema

-- Drop old indexes
DROP INDEX IF EXISTS idx_sessions_user;
DROP INDEX IF EXISTS idx_sessions_token;
DROP INDEX IF EXISTS idx_sessions_expires;

-- Drop old columns if they exist
ALTER TABLE user_sessions DROP COLUMN IF EXISTS session_token;
ALTER TABLE user_sessions DROP COLUMN IF EXISTS redis_key;
ALTER TABLE user_sessions DROP COLUMN IF EXISTS is_active;
ALTER TABLE user_sessions DROP COLUMN IF EXISTS invalidated_at;
ALTER TABLE user_sessions DROP COLUMN IF EXISTS invalidation_reason;

-- Add new refresh_token column
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS refresh_token VARCHAR(500);

-- Update ip_address type if needed (from INET to VARCHAR)
ALTER TABLE user_sessions ALTER COLUMN ip_address TYPE VARCHAR(45) USING ip_address::text;

-- Make columns NOT NULL if they aren't already
ALTER TABLE user_sessions ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE user_sessions ALTER COLUMN last_activity_at SET NOT NULL;

-- Create new indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_refresh_token ON user_sessions(refresh_token);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_refresh_token_unique ON user_sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

-- Add comment
COMMENT ON TABLE user_sessions IS 'User sessions with refresh tokens';
