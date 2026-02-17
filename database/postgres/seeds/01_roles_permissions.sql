-- Seed Data: Roles and Permissions
-- See auth schema for initial roles/permissions INSERT statements

-- ============================================================================
-- EXAMPLE DATA (Optional - for testing)
-- ============================================================================

-- Create a test admin user (password: 'test123' - hash generated with bcrypt)
INSERT INTO users (email, password_hash, username, first_name, last_name, is_active, email_verified, state)
VALUES (
    'admin@medicinalplants.mx',
    '$2a$10$YourHashedPasswordHere', -- Replace with actual bcrypt hash
    'admin',
    'System',
    'Administrator',
    TRUE,
    TRUE,
    'Ciudad de México'
);

-- Assign admin role
DO $
DECLARE
    v_user_id UUID;
    v_admin_role_id UUID;
BEGIN
    SELECT id INTO v_user_id FROM users WHERE email = 'admin@medicinalplants.mx';
    SELECT id INTO v_admin_role_id FROM roles WHERE name = 'ADMIN';
    
    INSERT INTO user_roles (user_id, role_id, assigned_by)
    VALUES (v_user_id, v_admin_role_id, v_user_id);
END $;

-- ============================================================================
-- SCHEDULED JOBS (Use pg_cron extension or external scheduler)
-- ============================================================================

-- Refresh analytics views daily at 2 AM
-- SELECT cron.schedule('refresh-analytics', '0 2 * * *', 'SELECT refresh_analytics_views()');

-- Cleanup expired sessions hourly
-- SELECT cron.schedule('cleanup-sessions', '0 * * * *', 'SELECT cleanup_expired_sessions()');

-- Cleanup expired cache every 6 hours
-- SELECT cron.schedule('cleanup-cache', '0 */6 * * *', 'SELECT cleanup_expired_cache()');

