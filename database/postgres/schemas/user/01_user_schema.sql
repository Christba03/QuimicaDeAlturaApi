-- User Database Schema
-- Sistema Inteligente de Análisis de Plantas Medicinales de México

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USER INTERACTION TRACKING
-- ============================================================================

-- Search history
CREATE TABLE user_search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Search query
    search_query TEXT NOT NULL,
    search_type VARCHAR(50), -- 'plant_name', 'symptom', 'compound', 'region', etc.
    filters_applied JSONB, -- Region, verification status, etc.
    
    -- Results
    results_count INTEGER,
    results_shown JSONB, -- Array of plant IDs shown
    
    -- User interaction
    clicked_result_id UUID REFERENCES plants(id),
    click_position INTEGER, -- Position in results (1st, 2nd, etc.)
    time_to_click INTERVAL,
    
    -- Context
    user_location JSONB, -- {state, city, lat, lng}
    device_type VARCHAR(50),
    
    -- Timestamp
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_history_user ON user_search_history(user_id, searched_at DESC);
CREATE INDEX idx_search_history_query ON user_search_history USING gin(to_tsvector('spanish', search_query));
CREATE INDEX idx_search_history_type ON user_search_history(search_type);
CREATE INDEX idx_search_history_clicked ON user_search_history(clicked_result_id) WHERE clicked_result_id IS NOT NULL;

COMMENT ON TABLE user_search_history IS 'Complete search analytics for query optimization and ranking';

-- Plant views
CREATE TABLE user_plant_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE, -- NULL for anonymous
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    
    -- View details
    view_duration INTERVAL, -- How long they viewed
    sections_viewed JSONB, -- Which sections: compounds, activities, references
    depth_score NUMERIC(3,2), -- How deep did they scroll (0-1)
    
    -- Context
    referrer_url TEXT,
    came_from_search BOOLEAN DEFAULT FALSE,
    search_query TEXT,
    
    -- Device
    device_type VARCHAR(50),
    user_agent TEXT,
    
    -- Location
    user_location JSONB,
    
    -- Session
    session_id UUID REFERENCES user_sessions(id),
    
    -- Timestamp
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plant_views_user ON user_plant_views(user_id, viewed_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX idx_plant_views_plant ON user_plant_views(plant_id, viewed_at DESC);
CREATE INDEX idx_plant_views_session ON user_plant_views(session_id) WHERE session_id IS NOT NULL;

-- Favorites
CREATE TABLE user_plant_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    
    -- Organization
    tags JSONB DEFAULT '[]', -- User-defined tags
    notes TEXT, -- User's personal notes
    
    -- Timestamps
    favorited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    unfavorited_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(user_id, plant_id)
);

CREATE INDEX idx_favorites_user ON user_plant_favorites(user_id, favorited_at DESC) WHERE is_active = TRUE;
CREATE INDEX idx_favorites_plant ON user_plant_favorites(plant_id) WHERE is_active = TRUE;
CREATE INDEX idx_favorites_tags ON user_plant_favorites USING GIN(tags) WHERE is_active = TRUE;

-- Usage reports (critical for effectiveness tracking)
CREATE TABLE user_plant_usage_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES medicinal_activities(id) ON DELETE SET NULL,
    
    -- Usage details
    plant_part_used VARCHAR(100),
    preparation_method preparation_method NOT NULL,
    preparation_details TEXT,
    
    -- Dosage
    dosage_amount NUMERIC(10,2),
    dosage_unit VARCHAR(50),
    frequency VARCHAR(100), -- 'once daily', 'three times daily', 'as needed'
    
    -- Duration
    start_date DATE,
    end_date DATE,
    duration_days INTEGER,
    
    -- Purpose
    condition_treated TEXT NOT NULL,
    symptoms_before TEXT,
    
    -- Effectiveness
    effectiveness_rating effectiveness_rating NOT NULL,
    symptoms_after TEXT,
    improvement_description TEXT,
    time_to_effect INTERVAL, -- How long until they noticed improvement
    
    -- Additional context
    concurrent_treatments TEXT, -- Other treatments used simultaneously
    user_age_range VARCHAR(20),
    user_gender VARCHAR(20),
    
    -- Side effects (if any)
    side_effects_observed BOOLEAN DEFAULT FALSE,
    side_effects_description TEXT,
    
    -- Verification
    verified_by_researcher UUID REFERENCES users(id),
    verification_notes TEXT,
    is_clinically_significant BOOLEAN,
    
    -- Status
    is_public BOOLEAN DEFAULT TRUE, -- User can choose to make private
    is_featured BOOLEAN DEFAULT FALSE, -- Exceptional reports
    
    -- Metadata
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_reports_user ON user_plant_usage_reports(user_id, reported_at DESC);
CREATE INDEX idx_usage_reports_plant ON user_plant_usage_reports(plant_id, reported_at DESC);
CREATE INDEX idx_usage_reports_activity ON user_plant_usage_reports(activity_id) WHERE activity_id IS NOT NULL;
CREATE INDEX idx_usage_reports_effectiveness ON user_plant_usage_reports(effectiveness_rating);
CREATE INDEX idx_usage_reports_public ON user_plant_usage_reports(is_public, is_featured) WHERE is_public = TRUE;

COMMENT ON TABLE user_plant_usage_reports IS 'Real-world usage data for effectiveness validation';

-- Comments and reviews
CREATE TABLE user_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plant_id UUID REFERENCES plants(id) ON DELETE CASCADE,
    
    -- Comment data
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(50), -- 'review', 'question', 'experience', 'correction'
    
    -- Rating (optional)
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    
    -- Threading
    parent_comment_id UUID REFERENCES user_comments(id) ON DELETE CASCADE,
    thread_depth INTEGER DEFAULT 0,
    
    -- Moderation
    is_moderated BOOLEAN DEFAULT FALSE,
    moderation_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'flagged'
    moderated_by UUID REFERENCES users(id),
    moderated_at TIMESTAMP WITH TIME ZONE,
    moderation_reason TEXT,
    
    -- User engagement
    helpful_count INTEGER DEFAULT 0,
    unhelpful_count INTEGER DEFAULT 0,
    
    -- Status
    is_edited BOOLEAN DEFAULT FALSE,
    edited_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deletion_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_user ON user_comments(user_id, created_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_comments_plant ON user_comments(plant_id, created_at DESC) WHERE is_deleted = FALSE AND plant_id IS NOT NULL;
CREATE INDEX idx_comments_parent ON user_comments(parent_comment_id) WHERE parent_comment_id IS NOT NULL;
CREATE INDEX idx_comments_moderation ON user_comments(moderation_status) WHERE is_deleted = FALSE;

-- Comment helpfulness votes
CREATE TABLE comment_votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    comment_id UUID NOT NULL REFERENCES user_comments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    vote_type VARCHAR(20) NOT NULL, -- 'helpful', 'unhelpful'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(comment_id, user_id)
);

CREATE INDEX idx_comment_votes_comment ON comment_votes(comment_id);
CREATE INDEX idx_comment_votes_user ON comment_votes(user_id);

-- Effectiveness reports (simplified separate table for easier analytics)
CREATE TABLE user_effectiveness_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    usage_report_id UUID REFERENCES user_plant_usage_reports(id) ON DELETE CASCADE,
    
    -- Simple effectiveness tracking
    worked BOOLEAN NOT NULL,
    effectiveness_rating effectiveness_rating,
    
    -- Quick feedback
    would_recommend BOOLEAN,
    brief_description TEXT,
    
    -- Metadata
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_effectiveness_plant ON user_effectiveness_reports(plant_id, worked);
CREATE INDEX idx_effectiveness_user ON user_effectiveness_reports(user_id);

-- Side effect reports
CREATE TABLE user_side_effect_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    usage_report_id UUID REFERENCES user_plant_usage_reports(id) ON DELETE CASCADE,
    
    -- Side effect details
    side_effect_description TEXT NOT NULL,
    severity severity_level NOT NULL,
    onset_time INTERVAL, -- Time after consumption
    duration INTERVAL,
    
    -- Context
    dosage_when_occurred TEXT,
    preparation_method preparation_method,
    
    -- Medical attention
    required_medical_attention BOOLEAN DEFAULT FALSE,
    medical_outcome TEXT,
    
    -- Verification
    verified_by_medical_professional BOOLEAN DEFAULT FALSE,
    verifying_researcher UUID REFERENCES users(id),
    
    -- Status
    is_public BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_side_effects_plant ON user_side_effect_reports(plant_id, severity);
CREATE INDEX idx_side_effects_user ON user_side_effect_reports(user_id);
CREATE INDEX idx_side_effects_severity ON user_side_effect_reports(severity);

COMMENT ON TABLE user_side_effect_reports IS 'Safety monitoring through user-reported adverse effects';

-- ============================================================================
-- SPONSORSHIP & MONETIZATION
-- ============================================================================

CREATE TABLE sponsors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Sponsor information
    company_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    logo_url TEXT,
    website_url TEXT,
    
    -- Contact
    contact_email CITEXT,
    contact_phone VARCHAR(50),
    contact_person VARCHAR(255),
    
    -- Business details
    business_type VARCHAR(100), -- 'manufacturer', 'retailer', 'research_institution'
    tax_id VARCHAR(100),
    
    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Contract
    contract_start_date DATE,
    contract_end_date DATE,
    contract_terms JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    suspended_at TIMESTAMP WITH TIME ZONE,
    suspension_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sponsors_active ON sponsors(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_sponsors_contract ON sponsors(contract_end_date) WHERE is_active = TRUE;

CREATE TABLE sponsored_plants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sponsor_id UUID NOT NULL REFERENCES sponsors(id) ON DELETE CASCADE,
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    
    -- Sponsorship details
    sponsorship_type VARCHAR(50), -- 'featured', 'promoted', 'research_funded'
    display_priority INTEGER DEFAULT 0, -- Higher = more prominent
    
    -- Redirect/affiliate
    redirect_url TEXT,
    affiliate_code VARCHAR(100),
    
    -- Disclosure
    disclosure_text TEXT NOT NULL, -- Required transparency text
    
    -- Budget & tracking
    daily_budget NUMERIC(10,2),
    total_budget NUMERIC(10,2),
    cost_per_click NUMERIC(10,2),
    spent_to_date NUMERIC(10,2) DEFAULT 0,
    
    -- Performance metrics (denormalized)
    impression_count BIGINT DEFAULT 0,
    click_count BIGINT DEFAULT 0,
    conversion_count BIGINT DEFAULT 0,
    
    -- Validity
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sponsor_id, plant_id)
);

CREATE INDEX idx_sponsored_plants_sponsor ON sponsored_plants(sponsor_id) WHERE is_active = TRUE;
CREATE INDEX idx_sponsored_plants_plant ON sponsored_plants(plant_id) WHERE is_active = TRUE;
CREATE INDEX idx_sponsored_plants_priority ON sponsored_plants(display_priority DESC) WHERE is_active = TRUE;
CREATE INDEX idx_sponsored_plants_validity ON sponsored_plants(valid_until) WHERE is_active = TRUE;

CREATE TABLE sponsored_compounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sponsor_id UUID NOT NULL REFERENCES sponsors(id) ON DELETE CASCADE,
    compound_id UUID NOT NULL REFERENCES chemical_compounds(id) ON DELETE CASCADE,
    
    -- Similar structure to sponsored_plants
    sponsorship_type VARCHAR(50),
    display_priority INTEGER DEFAULT 0,
    redirect_url TEXT,
    affiliate_code VARCHAR(100),
    disclosure_text TEXT NOT NULL,
    
    daily_budget NUMERIC(10,2),
    total_budget NUMERIC(10,2),
    cost_per_click NUMERIC(10,2),
    spent_to_date NUMERIC(10,2) DEFAULT 0,
    
    impression_count BIGINT DEFAULT 0,
    click_count BIGINT DEFAULT 0,
    conversion_count BIGINT DEFAULT 0,
    
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sponsor_id, compound_id)
);

CREATE INDEX idx_sponsored_compounds_sponsor ON sponsored_compounds(sponsor_id) WHERE is_active = TRUE;
CREATE INDEX idx_sponsored_compounds_compound ON sponsored_compounds(compound_id) WHERE is_active = TRUE;

-- Click tracking
CREATE TABLE sponsor_clicks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What was clicked
    sponsored_plant_id UUID REFERENCES sponsored_plants(id) ON DELETE CASCADE,
    sponsored_compound_id UUID REFERENCES sponsored_compounds(id) ON DELETE CASCADE,
    
    -- Who clicked
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    
    -- Context
    plant_id UUID REFERENCES plants(id),
    compound_id UUID REFERENCES chemical_compounds(id),
    page_url TEXT,
    position_on_page VARCHAR(100), -- 'top_banner', 'sidebar', 'inline_result'
    
    -- Device & location
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50),
    user_location JSONB,
    
    -- Attribution
    referrer_url TEXT,
    utm_parameters JSONB,
    
    -- Timestamp
    clicked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sponsor_clicks_plant ON sponsor_clicks(sponsored_plant_id, clicked_at DESC) WHERE sponsored_plant_id IS NOT NULL;
CREATE INDEX idx_sponsor_clicks_compound ON sponsor_clicks(sponsored_compound_id, clicked_at DESC) WHERE sponsored_compound_id IS NOT NULL;
CREATE INDEX idx_sponsor_clicks_user ON sponsor_clicks(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_sponsor_clicks_timestamp ON sponsor_clicks(clicked_at DESC);

-- Conversion tracking
CREATE TABLE sponsor_conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sponsor_click_id UUID NOT NULL REFERENCES sponsor_clicks(id) ON DELETE CASCADE,
    
    -- Conversion details
    conversion_type VARCHAR(50), -- 'purchase', 'signup', 'download', 'contact'
    conversion_value NUMERIC(10,2),
    conversion_currency VARCHAR(3) DEFAULT 'MXN',
    
    -- Attribution
    time_to_conversion INTERVAL,
    
    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    converted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    conversion_metadata JSONB
);

CREATE INDEX idx_conversions_click ON sponsor_conversions(sponsor_click_id);
CREATE INDEX idx_conversions_timestamp ON sponsor_conversions(converted_at DESC);

-- Recommendation algorithm decision log
CREATE TABLE recommendation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    
    -- Request context
    query TEXT,
    filters JSONB,
    user_location JSONB,
    
    -- Recommendation algorithm
    algorithm_version VARCHAR(50),
    recommendation_type recommendation_type,
    
    -- Results returned
    organic_results JSONB, -- Array of {plant_id, score, rank}
    sponsored_results JSONB, -- Array of {plant_id, sponsor_id, rank, bid}
    final_results JSONB, -- Merged and ranked final results
    
    -- Scoring details (for transparency and debugging)
    scoring_breakdown JSONB,
    /* Example:
    {
        "relevance_score": 0.85,
        "evidence_score": 0.90,
        "user_effectiveness_score": 0.75,
        "regional_relevance": 0.95,
        "sponsor_boost": 0.10
    }
    */
    
    -- Performance
    query_execution_time INTERVAL,
    
    -- Timestamp
    recommended_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendation_logs_user ON recommendation_logs(user_id, recommended_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX idx_recommendation_logs_type ON recommendation_logs(recommendation_type);
CREATE INDEX idx_recommendation_logs_timestamp ON recommendation_logs(recommended_at DESC);

COMMENT ON TABLE recommendation_logs IS 'Audit trail for recommendation algorithm decisions and sponsored content disclosure';



-- ============================================================================
-- AUDIT & DATA QUALITY
-- ============================================================================

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What happened
    table_name VARCHAR(255) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE', 'VERIFY', 'APPROVE', 'REJECT'
    
    -- Changes
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB, -- Array of field names
    
    -- Who and when
    user_id UUID REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    
    -- Context
    operation_context JSONB,
    reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id, created_at DESC);
CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);
CREATE INDEX idx_audit_timestamp ON audit_log(created_at DESC);

-- Partitioning recommendation for audit_log (by month)
-- ALTER TABLE audit_log PARTITION BY RANGE (created_at);

COMMENT ON TABLE audit_log IS 'Universal audit trail for all data changes';

CREATE TABLE data_quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What is being measured
    entity_type VARCHAR(100), -- 'plant', 'compound', 'article', etc.
    entity_id UUID NOT NULL,
    
    -- Quality dimensions
    completeness_score NUMERIC(3,2) CHECK (completeness_score BETWEEN 0 AND 1),
    accuracy_score NUMERIC(3,2) CHECK (accuracy_score BETWEEN 0 AND 1),
    consistency_score NUMERIC(3,2) CHECK (consistency_score BETWEEN 0 AND 1),
    timeliness_score NUMERIC(3,2) CHECK (timeliness_score BETWEEN 0 AND 1),
    
    -- Overall quality
    overall_quality_score NUMERIC(3,2) GENERATED ALWAYS AS (
        (completeness_score + accuracy_score + consistency_score + timeliness_score) / 4
    ) STORED,
    
    -- Detailed metrics
    metrics_breakdown JSONB,
    /* Example:
    {
        "missing_fields": ["habitat_description", "flowering_season"],
        "outdated_fields": ["conservation_status"],
        "conflicting_sources": 0,
        "citation_count": 12,
        "verification_status": "verified"
    }
    */
    
    -- Issues identified
    quality_issues JSONB DEFAULT '[]',
    
    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculation_version VARCHAR(50)
);

CREATE INDEX idx_quality_metrics_entity ON data_quality_metrics(entity_type, entity_id);
CREATE INDEX idx_quality_metrics_score ON data_quality_metrics(overall_quality_score DESC);

COMMENT ON TABLE data_quality_metrics IS 'Data quality scoring for continuous improvement';

