-- ============================================================================
-- FUNCTIONS AND PROCEDURES
-- ============================================================================

-- Update search vector for plants
CREATE OR REPLACE FUNCTION update_plant_search_vector()
RETURNS TRIGGER AS $
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('spanish', COALESCE(NEW.scientific_name, '')), 'A') ||
        setweight(to_tsvector('spanish', COALESCE(
            (SELECT string_agg(name, ' ') FROM plant_names WHERE plant_id = NEW.id)
        , '')), 'B');
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER tg_update_plant_search_vector
BEFORE INSERT OR UPDATE ON plants
FOR EACH ROW
EXECUTE FUNCTION update_plant_search_vector();

-- Update compound search vector
CREATE OR REPLACE FUNCTION update_compound_search_vector()
RETURNS TRIGGER AS $
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.compound_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.iupac_name, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.synonyms::text, '')), 'C');
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER tg_update_compound_search_vector
BEFORE INSERT OR UPDATE ON chemical_compounds
FOR EACH ROW
EXECUTE FUNCTION update_compound_search_vector();

-- Update article search vector
CREATE OR REPLACE FUNCTION update_article_search_vector()
RETURNS TRIGGER AS $
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.abstract, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.keywords::text, '')), 'C');
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER tg_update_article_search_vector
BEFORE INSERT OR UPDATE ON scientific_articles
FOR EACH ROW
EXECUTE FUNCTION update_article_search_vector();

-- Auto-update updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER tg_update_plants_updated_at BEFORE UPDATE ON plants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tg_update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tg_update_compounds_updated_at BEFORE UPDATE ON chemical_compounds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tg_update_articles_updated_at BEFORE UPDATE ON scientific_articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit log trigger
CREATE OR REPLACE FUNCTION log_audit_trail()
RETURNS TRIGGER AS $
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, user_id)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD), current_setting('app.current_user_id', TRUE)::uuid);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), current_setting('app.current_user_id', TRUE)::uuid);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, new_values, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW), current_setting('app.current_user_id', TRUE)::uuid);
        RETURN NEW;
    END IF;
END;
$ LANGUAGE plpgsql;

-- Apply audit triggers to key tables
CREATE TRIGGER tg_audit_plants AFTER INSERT OR UPDATE OR DELETE ON plants
    FOR EACH ROW EXECUTE FUNCTION log_audit_trail();

CREATE TRIGGER tg_audit_plant_compounds AFTER INSERT OR UPDATE OR DELETE ON plant_compounds
    FOR EACH ROW EXECUTE FUNCTION log_audit_trail();

CREATE TRIGGER tg_audit_plant_activities AFTER INSERT OR UPDATE OR DELETE ON plant_activities
    FOR EACH ROW EXECUTE FUNCTION log_audit_trail();

-- Increment plant view count
CREATE OR REPLACE FUNCTION increment_plant_view_count()
RETURNS TRIGGER AS $
BEGIN
    UPDATE plants 
    SET view_count = view_count + 1 
    WHERE id = NEW.plant_id;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER tg_increment_plant_views AFTER INSERT ON user_plant_views
    FOR EACH ROW EXECUTE FUNCTION increment_plant_view_count();

-- Update favorite count
CREATE OR REPLACE FUNCTION update_plant_favorite_count()
RETURNS TRIGGER AS $
BEGIN
    IF TG_OP = 'INSERT' AND NEW.is_active = TRUE THEN
        UPDATE plants SET favorite_count = favorite_count + 1 WHERE id = NEW.plant_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.is_active = TRUE AND NEW.is_active = FALSE THEN
        UPDATE plants SET favorite_count = favorite_count - 1 WHERE id = NEW.plant_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.is_active = FALSE AND NEW.is_active = TRUE THEN
        UPDATE plants SET favorite_count = favorite_count + 1 WHERE id = NEW.plant_id;
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER tg_update_plant_favorite_count 
AFTER INSERT OR UPDATE ON user_plant_favorites
FOR EACH ROW EXECUTE FUNCTION update_plant_favorite_count();

-- Permission check function
CREATE OR REPLACE FUNCTION user_has_permission(
    p_user_id UUID,
    p_resource_type resource_type,
    p_action permission_action
)
RETURNS BOOLEAN AS $
DECLARE
    has_perm BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM user_roles ur
        JOIN role_permissions rp ON ur.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE ur.user_id = p_user_id
            AND ur.is_active = TRUE
            AND (ur.valid_until IS NULL OR ur.valid_until > CURRENT_TIMESTAMP)
            AND rp.is_granted = TRUE
            AND p.resource_type = p_resource_type
            AND p.action = p_action
            AND p.is_active = TRUE
    ) INTO has_perm;
    
    RETURN has_perm;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION user_has_permission IS 'Check if user has specific permission based on their roles';

-- Calculate plant data completeness score
CREATE OR REPLACE FUNCTION calculate_plant_completeness(p_plant_id UUID)
RETURNS NUMERIC AS $
DECLARE
    v_score NUMERIC := 0;
    v_weight NUMERIC;
BEGIN
    -- Scientific name (required, but check quality)
    IF EXISTS (SELECT 1 FROM plants WHERE id = p_plant_id AND scientific_name IS NOT NULL) THEN
        v_score := v_score + 0.05;
    END IF;
    
    -- Common names
    IF EXISTS (SELECT 1 FROM plant_names WHERE plant_id = p_plant_id LIMIT 1) THEN
        v_score := v_score + 0.05;
    END IF;
    
    -- Geographic data
    IF EXISTS (SELECT 1 FROM plants WHERE id = p_plant_id AND mexican_states IS NOT NULL) THEN
        v_score := v_score + 0.10;
    END IF;
    
    -- Compounds
    SELECT COUNT(*)::numeric * 0.05 INTO v_weight
    FROM plant_compounds WHERE plant_id = p_plant_id AND deleted_at IS NULL;
    v_score := v_score + LEAST(v_weight, 0.20); -- Cap at 0.20
    
    -- Activities
    SELECT COUNT(*)::numeric * 0.05 INTO v_weight
    FROM plant_activities WHERE plant_id = p_plant_id AND deleted_at IS NULL;
    v_score := v_score + LEAST(v_weight, 0.20); -- Cap at 0.20
    
    -- Scientific articles
    SELECT COUNT(*)::numeric * 0.03 INTO v_weight
    FROM article_plant_associations WHERE plant_id = p_plant_id;
    v_score := v_score + LEAST(v_weight, 0.15); -- Cap at 0.15
    
    -- Images
    IF EXISTS (SELECT 1 FROM plant_images WHERE plant_id = p_plant_id LIMIT 1) THEN
        v_score := v_score + 0.05;
    END IF;
    
    -- Genomic data
    IF EXISTS (SELECT 1 FROM genomic_sequences WHERE plant_id = p_plant_id LIMIT 1) THEN
        v_score := v_score + 0.10;
    END IF;
    
    -- Verification status
    IF EXISTS (SELECT 1 FROM plants WHERE id = p_plant_id AND verification_status = 'VERIFIED') THEN
        v_score := v_score + 0.10;
    END IF;
    
    RETURN LEAST(v_score, 1.0);
END;
$ LANGUAGE plpgsql;

-- Refresh materialized views function
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_most_searched_plants;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_most_viewed_plants;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_most_favorited_plants;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_most_used_plants;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_high_effectiveness_low_evidence;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_regional_usage_trends;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sponsor_performance;
END;
$ LANGUAGE plpgsql;

-- Cleanup expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $
BEGIN
    UPDATE user_sessions
    SET is_active = FALSE,
        invalidated_at = CURRENT_TIMESTAMP,
        invalidation_reason = 'expired'
    WHERE expires_at < CURRENT_TIMESTAMP
        AND is_active = TRUE;
END;
$ LANGUAGE plpgsql;

-- Cleanup expired cache
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $
BEGIN
    DELETE FROM api_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$ LANGUAGE plpgsql;

