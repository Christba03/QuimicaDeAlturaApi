-- Chatbot Database Schema
-- Sistema Inteligente de Análisis de Plantas Medicinales de México

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CHATBOT & CONVERSATION MANAGEMENT
-- Add this to your existing schema
-- ============================================================================

-- ============================================================================
-- CHATBOT ENUMS
-- ============================================================================

CREATE TYPE conversation_status AS ENUM (
    'ACTIVE',
    'RESOLVED',
    'ARCHIVED',
    'ESCALATED_TO_RESEARCHER',
    'ESCALATED_TO_SUPPORT',
    'ABANDONED'
);

CREATE TYPE message_type AS ENUM (
    'USER_TEXT',
    'USER_VOICE',
    'USER_IMAGE',
    'BOT_TEXT',
    'BOT_IMAGE',
    'BOT_CARD',
    'BOT_RECOMMENDATION',
    'SYSTEM_MESSAGE',
    'ESCALATION_HANDOFF'
);

CREATE TYPE message_intent AS ENUM (
    'PLANT_SEARCH',
    'SYMPTOM_QUERY',
    'PREPARATION_QUESTION',
    'DOSAGE_QUESTION',
    'SIDE_EFFECTS_INQUIRY',
    'COMPOUND_LOOKUP',
    'REGION_SPECIFIC',
    'GENERAL_QUESTION',
    'EFFECTIVENESS_FEEDBACK',
    'REPORT_USAGE',
    'SMALL_TALK',
    'UNKNOWN'
);

CREATE TYPE interaction_action AS ENUM (
    'VIEWED_PLANT',
    'CLICKED_RECOMMENDATION',
    'SAVED_FAVORITE',
    'SHARED_RESULT',
    'REQUESTED_MORE_INFO',
    'SUBMITTED_FEEDBACK',
    'ESCALATED_TO_HUMAN',
    'DOWNLOADED_RESOURCE'
);

CREATE TYPE sentiment_score AS ENUM (
    'VERY_NEGATIVE',
    'NEGATIVE',
    'NEUTRAL',
    'POSITIVE',
    'VERY_POSITIVE'
);

-- ============================================================================
-- CONVERSATIONS
-- ============================================================================

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- NULL for anonymous
    session_id UUID,
    
    -- Conversation metadata
    conversation_title VARCHAR(500), -- Auto-generated from first message
    conversation_status conversation_status DEFAULT 'ACTIVE',
    
    -- Context
    initial_intent message_intent,
    primary_topic VARCHAR(255), -- 'headache treatment', 'diabetes management', etc.
    plants_discussed JSONB DEFAULT '[]', -- Array of plant IDs mentioned
    compounds_discussed JSONB DEFAULT '[]', -- Array of compound IDs
    
    -- User context at conversation start
    user_location JSONB, -- {state, city, lat, lng}
    user_language VARCHAR(10) DEFAULT 'es',
    user_preferences JSONB, -- Collected preferences during chat
    
    -- Quality metrics
    user_satisfaction_score INTEGER CHECK (user_satisfaction_score BETWEEN 1 AND 5),
    user_sentiment sentiment_score,
    bot_confidence_avg NUMERIC(3,2), -- Average confidence across messages
    
    -- Escalation
    escalated_to_researcher_id UUID,
    escalation_reason TEXT,
    escalated_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID,
    
    -- Analytics
    message_count INTEGER DEFAULT 0,
    user_message_count INTEGER DEFAULT 0,
    bot_message_count INTEGER DEFAULT 0,
    total_duration INTERVAL, -- Time from first to last message
    avg_response_time INTERVAL, -- Bot's average response time
    
    -- Recommendations made
    plants_recommended JSONB DEFAULT '[]', -- Array of {plant_id, confidence, timestamp}
    recommendation_clicked BOOLEAN DEFAULT FALSE,
    recommendation_favorited BOOLEAN DEFAULT FALSE,
    
    -- Device & channel
    channel VARCHAR(50) DEFAULT 'web', -- 'web', 'mobile', 'whatsapp', 'api'
    device_type VARCHAR(50),
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- Archival
    archived_at TIMESTAMP WITH TIME ZONE,
    
    -- Full-text search
    search_vector tsvector
);

CREATE INDEX idx_conversations_user ON conversations(user_id, started_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX idx_conversations_session ON conversations(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX idx_conversations_status ON conversations(conversation_status, last_message_at DESC);
CREATE INDEX idx_conversations_intent ON conversations(initial_intent);
CREATE INDEX idx_conversations_plants ON conversations USING GIN(plants_discussed);
CREATE INDEX idx_conversations_search ON conversations USING GIN(search_vector);
CREATE INDEX idx_conversations_started ON conversations(started_at DESC);

COMMENT ON TABLE conversations IS 'Chatbot conversation sessions with context and analytics';

-- ============================================================================
-- MESSAGES
-- ============================================================================

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message identification
    message_sequence INTEGER NOT NULL, -- Order within conversation
    parent_message_id UUID REFERENCES messages(id), -- For threaded/follow-up questions
    
    -- Message content
    message_type message_type NOT NULL,
    message_text TEXT,
    message_metadata JSONB, -- Voice transcription, image analysis, etc.
    
    -- Rich content (for bot responses)
    rich_content JSONB,
    /* Example for BOT_RECOMMENDATION:
    {
        "type": "plant_recommendation",
        "plant_id": "uuid",
        "confidence": 0.92,
        "reasoning": "Based on your symptoms...",
        "image_url": "...",
        "quick_actions": [
            {"label": "Ver más", "action": "view_plant"},
            {"label": "Guardar", "action": "favorite"}
        ]
    }
    */
    
    -- Intent & entities (NLP extraction)
    detected_intent message_intent,
    intent_confidence NUMERIC(3,2),
    extracted_entities JSONB,
    /* Example:
    {
        "symptoms": ["dolor de cabeza", "náuseas"],
        "location": "Oaxaca",
        "preparation": "té",
        "plant_names": ["manzanilla", "árnica"]
    }
    */
    
    -- Sender
    is_from_user BOOLEAN NOT NULL,
    user_id UUID, -- Who sent it (if user message)
    bot_version VARCHAR(50), -- Which bot version generated this (if bot message)
    model_used VARCHAR(100), -- 'gpt-4', 'claude-3', 'custom-rag', etc.
    
    -- Bot response quality
    confidence_score NUMERIC(3,2), -- Bot's confidence in its response
    needs_verification BOOLEAN DEFAULT FALSE, -- Flagged for researcher review
    verified_by UUID,
    verification_notes TEXT,
    
    -- User feedback on bot message
    user_feedback_helpful BOOLEAN,
    user_feedback_text TEXT,
    feedback_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Processing metadata
    processing_time INTERVAL, -- Time to generate response
    retrieval_sources JSONB, -- Which documents/articles were used
    /* Example:
    {
        "rag_documents": ["article_uuid_1", "plant_uuid_2"],
        "external_apis": ["pubmed", "kegg"],
        "confidence_breakdown": {
            "retrieval": 0.88,
            "generation": 0.95
        }
    }
    */
    
    -- Interaction tracking
    user_interacted BOOLEAN DEFAULT FALSE, -- Did user click/interact with this message?
    interaction_type interaction_action,
    interaction_metadata JSONB,
    
    -- Timestamps
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    
    -- Constraints
    UNIQUE(conversation_id, message_sequence)
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, message_sequence) WHERE deleted_at IS NULL;
CREATE INDEX idx_messages_user ON messages(user_id, sent_at DESC) WHERE user_id IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_messages_intent ON messages(detected_intent) WHERE deleted_at IS NULL;
CREATE INDEX idx_messages_needs_verification ON messages(needs_verification) WHERE needs_verification = TRUE;
CREATE INDEX idx_messages_feedback ON messages(user_feedback_helpful) WHERE user_feedback_helpful IS NOT NULL;
CREATE INDEX idx_messages_entities ON messages USING GIN(extracted_entities) WHERE deleted_at IS NULL;

COMMENT ON TABLE messages IS 'Individual messages within conversations with NLP analysis and feedback';

-- ============================================================================
-- CHATBOT KNOWLEDGE BASE (RAG)
-- ============================================================================

CREATE TABLE chatbot_knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Document identification
    document_title VARCHAR(500) NOT NULL,
    document_type VARCHAR(100), -- 'faq', 'plant_summary', 'preparation_guide', 'safety_info'
    
    -- Content
    content TEXT NOT NULL,
    structured_content JSONB, -- Parsed Q&A, sections, etc.
    
    -- Source
    source_type VARCHAR(100), -- 'manual', 'auto_generated', 'plant_data', 'article'
    source_id UUID, -- Reference to plant, article, etc.
    
    -- Language
    language VARCHAR(10) DEFAULT 'es',
    
    -- Vector embedding (for semantic search)
    embedding JSONB, -- was vector(1536), requires pgvector extension
    
    -- Metadata
    tags JSONB DEFAULT '[]',
    related_intents JSONB DEFAULT '[]', -- Which intents this document answers
    
    -- Quality
    usage_count INTEGER DEFAULT 0, -- How often retrieved
    helpful_count INTEGER DEFAULT 0, -- User feedback
    unhelpful_count INTEGER DEFAULT 0,
    quality_score NUMERIC(3,2),
    
    -- Verification
    verified_by UUID,
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Full-text search
    search_vector tsvector
);

CREATE INDEX idx_knowledge_type ON chatbot_knowledge_documents(document_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_knowledge_language ON chatbot_knowledge_documents(language) WHERE deleted_at IS NULL;
CREATE INDEX idx_knowledge_source ON chatbot_knowledge_documents(source_type, source_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_knowledge_search ON chatbot_knowledge_documents USING GIN(search_vector) WHERE deleted_at IS NULL;
-- Vector similarity index (requires pgvector extension)
-- CREATE INDEX idx_knowledge_embedding ON chatbot_knowledge_documents USING ivfflat (embedding vector_cosine_ops);

COMMENT ON TABLE chatbot_knowledge_documents IS 'RAG knowledge base for chatbot semantic search';

-- ============================================================================
-- CHATBOT QUICK REPLIES & PROMPTS
-- ============================================================================

CREATE TABLE chatbot_quick_replies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Reply configuration
    trigger_intent message_intent,
    trigger_context JSONB, -- Conditions when this should appear
    
    -- Reply options
    reply_text VARCHAR(500) NOT NULL,
    reply_action VARCHAR(100), -- 'search_plant', 'view_symptoms', 'ask_dosage'
    reply_payload JSONB, -- Data passed when clicked
    
    -- Display
    display_order INTEGER DEFAULT 0,
    icon VARCHAR(50), -- Emoji or icon name
    
    -- Language
    language VARCHAR(10) DEFAULT 'es',
    
    -- Analytics
    shown_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    click_through_rate NUMERIC(5,4) GENERATED ALWAYS AS (
        CASE WHEN shown_count > 0 
        THEN clicked_count::numeric / shown_count::numeric 
        ELSE 0 END
    ) STORED,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

CREATE INDEX idx_quick_replies_intent ON chatbot_quick_replies(trigger_intent) WHERE is_active = TRUE;
CREATE INDEX idx_quick_replies_language ON chatbot_quick_replies(language) WHERE is_active = TRUE;

-- ============================================================================
-- CONVERSATION CONTEXT (for multi-turn conversations)
-- ============================================================================

CREATE TABLE conversation_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Context tracking
    context_key VARCHAR(255) NOT NULL, -- 'current_plant', 'symptoms', 'location'
    context_value JSONB NOT NULL,
    
    -- Lifecycle
    set_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE, -- Auto-cleanup stale context
    
    -- Metadata
    set_by_message_id UUID REFERENCES messages(id),
    
    UNIQUE(conversation_id, context_key)
);

CREATE INDEX idx_context_conversation ON conversation_context(conversation_id);
CREATE INDEX idx_context_expires ON conversation_context(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE conversation_context IS 'Stateful context for multi-turn conversations';

-- ============================================================================
-- CHATBOT FEEDBACK & TRAINING
-- ========================================================================

CREATE TABLE chatbot_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID,
    
    -- Feedback type
    feedback_type VARCHAR(50), -- 'thumbs_up', 'thumbs_down', 'report_issue', 'suggest_improvement'
    
    -- Specific feedback
    issue_category VARCHAR(100), -- 'incorrect_info', 'irrelevant', 'offensive', 'not_helpful'
    feedback_text TEXT,
    
    -- What was wrong (for training)
    expected_response TEXT, -- What user expected
    suggested_improvement TEXT,
    
    -- Context snapshot
    conversation_context JSONB, -- Snapshot of conversation state
    
    -- Follow-up
    reviewed_by UUID,
    review_notes TEXT,
    action_taken VARCHAR(255), -- 'updated_knowledge_base', 'retrained_model', 'no_action'
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_conversation ON chatbot_feedback(conversation_id);
CREATE INDEX idx_feedback_message ON chatbot_feedback(message_id) WHERE message_id IS NOT NULL;
CREATE INDEX idx_feedback_type ON chatbot_feedback(feedback_type);
CREATE INDEX idx_feedback_reviewed ON chatbot_feedback(reviewed_by) WHERE reviewed_by IS NOT NULL;

COMMENT ON TABLE chatbot_feedback IS 'User feedback for chatbot improvement and training';

-- ============================================================================
-- CHATBOT ANALYTICS TABLES
-- ============================================================================

-- Intent detection accuracy tracking
CREATE TABLE intent_classification_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Classification results
    predicted_intent message_intent NOT NULL,
    confidence_score NUMERIC(3,2) NOT NULL,
    alternative_intents JSONB, -- Top 3 alternatives with scores
    
    -- Verification
    actual_intent message_intent, -- Manually verified
    verified_by UUID,
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Model info
    model_version VARCHAR(50),
    classification_method VARCHAR(100), -- 'regex', 'ml_model', 'llm'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_intent_log_message ON intent_classification_log(message_id);
CREATE INDEX idx_intent_log_predicted ON intent_classification_log(predicted_intent);
CREATE INDEX idx_intent_log_accuracy ON intent_classification_log(predicted_intent, actual_intent) 
    WHERE actual_intent IS NOT NULL;

COMMENT ON TABLE intent_classification_log IS 'Intent classification tracking for model accuracy monitoring';

-- Conversation flow patterns (for optimization)
CREATE TABLE conversation_flow_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    intent_sequence JSONB NOT NULL, -- Array of intents in order
    /* Example:
    ["SYMPTOM_QUERY", "PLANT_SEARCH", "PREPARATION_QUESTION", "DOSAGE_QUESTION"]
    */
    
    -- Analytics
    occurrence_count INTEGER DEFAULT 1,
    avg_satisfaction_score NUMERIC(3,2),
    avg_conversation_duration INTERVAL,
    conversion_rate NUMERIC(5,4), -- % that led to plant recommendation acceptance
    
    -- Pattern metadata
    typical_user_segment VARCHAR(100), -- 'first_time_user', 'power_user', etc.
    
    -- Status
    is_optimal BOOLEAN DEFAULT TRUE, -- False if leads to poor outcomes
    improvement_notes TEXT,
    
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_flow_patterns_sequence ON conversation_flow_patterns USING GIN(intent_sequence);
CREATE INDEX idx_flow_patterns_optimal ON conversation_flow_patterns(is_optimal);

COMMENT ON TABLE conversation_flow_patterns IS 'Common conversation patterns for UX optimization';

-- ============================================================================
-- MATERIALIZED VIEWS FOR CHATBOT ANALYTICS
-- ============================================================================

-- Chatbot performance metrics
CREATE MATERIALIZED VIEW mv_chatbot_performance AS
SELECT 
    DATE_TRUNC('day', started_at) AS date,
    COUNT(DISTINCT id) AS total_conversations,
    COUNT(DISTINCT user_id) FILTER (WHERE user_id IS NOT NULL) AS unique_users,
    
    -- Message metrics
    SUM(message_count) AS total_messages,
    ROUND(AVG(message_count), 2) AS avg_messages_per_conversation,
    ROUND(AVG(EXTRACT(EPOCH FROM total_duration)), 2) AS avg_duration_seconds,
    
    -- Quality metrics
    ROUND(AVG(user_satisfaction_score), 2) AS avg_satisfaction,
    COUNT(*) FILTER (WHERE user_satisfaction_score >= 4) AS satisfied_users,
    ROUND(
        COUNT(*) FILTER (WHERE user_satisfaction_score >= 4)::numeric / 
        NULLIF(COUNT(*) FILTER (WHERE user_satisfaction_score IS NOT NULL), 0) * 100,
        2
    ) AS satisfaction_rate,
    
    -- Escalation metrics
    COUNT(*) FILTER (WHERE conversation_status = 'ESCALATED_TO_RESEARCHER') AS escalated_count,
    ROUND(
        COUNT(*) FILTER (WHERE conversation_status = 'ESCALATED_TO_RESEARCHER')::numeric / 
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS escalation_rate,
    
    -- Conversion metrics
    COUNT(*) FILTER (WHERE recommendation_clicked = TRUE) AS recommendation_clicks,
    COUNT(*) FILTER (WHERE recommendation_favorited = TRUE) AS recommendation_saves,
    
    -- Intent distribution (computed separately to avoid nested aggregate)
    NULL::JSONB AS intent_distribution
FROM conversations
WHERE started_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', started_at)
ORDER BY date DESC;

CREATE UNIQUE INDEX ON mv_chatbot_performance (date);

-- Top performing knowledge base documents
CREATE MATERIALIZED VIEW mv_top_knowledge_documents AS
SELECT 
    id,
    document_title,
    document_type,
    language,
    usage_count,
    helpful_count,
    unhelpful_count,
    ROUND(
        CASE WHEN (helpful_count + unhelpful_count) > 0
        THEN helpful_count::numeric / (helpful_count + unhelpful_count)::numeric
        ELSE 0 END,
        3
    ) AS helpfulness_rate,
    quality_score,
    tags
FROM chatbot_knowledge_documents
WHERE deleted_at IS NULL
    AND usage_count > 0
ORDER BY usage_count DESC, helpfulness_rate DESC
LIMIT 100;

CREATE UNIQUE INDEX ON mv_top_knowledge_documents (id);

-- Most common user intents
CREATE MATERIALIZED VIEW mv_common_intents AS
SELECT 
    detected_intent,
    COUNT(*) AS message_count,
    COUNT(DISTINCT conversation_id) AS conversation_count,
    ROUND(AVG(intent_confidence), 3) AS avg_confidence,
    COUNT(*) FILTER (WHERE user_feedback_helpful = TRUE) AS helpful_responses,
    COUNT(*) FILTER (WHERE user_feedback_helpful = FALSE) AS unhelpful_responses,
    ROUND(
        COUNT(*) FILTER (WHERE user_feedback_helpful = TRUE)::numeric /
        NULLIF(COUNT(*) FILTER (WHERE user_feedback_helpful IS NOT NULL), 0),
        3
    ) AS helpfulness_rate
FROM messages
WHERE deleted_at IS NULL
    AND sent_at >= CURRENT_DATE - INTERVAL '30 days'
    AND is_from_user = FALSE
GROUP BY detected_intent
ORDER BY message_count DESC;

CREATE UNIQUE INDEX ON mv_common_intents (detected_intent);

-- ============================================================================
-- CHATBOT TRIGGERS
-- ============================================================================

-- Update conversation search vector
CREATE OR REPLACE FUNCTION update_conversation_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('spanish', COALESCE(NEW.conversation_title, '')), 'A') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.primary_topic, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_update_conversation_search_vector
BEFORE INSERT OR UPDATE ON conversations
FOR EACH ROW
EXECUTE FUNCTION update_conversation_search_vector();

-- Update knowledge document search vector
CREATE OR REPLACE FUNCTION update_knowledge_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('spanish', COALESCE(NEW.document_title, '')), 'A') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.content, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_update_knowledge_search_vector
BEFORE INSERT OR UPDATE ON chatbot_knowledge_documents
FOR EACH ROW
EXECUTE FUNCTION update_knowledge_search_vector();

-- Auto-update conversation metrics when messages are added
CREATE OR REPLACE FUNCTION update_conversation_metrics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET 
        message_count = message_count + 1,
        user_message_count = user_message_count + CASE WHEN NEW.is_from_user THEN 1 ELSE 0 END,
        bot_message_count = bot_message_count + CASE WHEN NOT NEW.is_from_user THEN 1 ELSE 0 END,
        last_message_at = NEW.sent_at,
        total_duration = NEW.sent_at - started_at,
        plants_discussed = COALESCE(plants_discussed, '[]'::jsonb) || 
            COALESCE(NEW.extracted_entities->'plant_ids', '[]'::jsonb)
    WHERE id = NEW.conversation_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_update_conversation_metrics
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION update_conversation_metrics();

-- Auto-generate conversation title from first message
CREATE OR REPLACE FUNCTION generate_conversation_title()
RETURNS TRIGGER AS $$
DECLARE
    v_title TEXT;
BEGIN
    IF NEW.message_sequence = 1 AND NEW.is_from_user THEN
        -- Use first 100 chars of user's first message as title
        v_title := SUBSTRING(NEW.message_text, 1, 100);
        IF LENGTH(NEW.message_text) > 100 THEN
            v_title := v_title || '...';
        END IF;
        
        UPDATE conversations
        SET 
            conversation_title = v_title,
            initial_intent = NEW.detected_intent
        WHERE id = NEW.conversation_id AND conversation_title IS NULL;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_generate_conversation_title
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION generate_conversation_title();

-- ============================================================================
-- CHATBOT FUNCTIONS
-- ============================================================================

-- Get conversation history with context
CREATE OR REPLACE FUNCTION get_conversation_history(
    p_conversation_id UUID,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    message_id UUID,
    message_sequence INTEGER,
    message_type message_type,
    message_text TEXT,
    is_from_user BOOLEAN,
    detected_intent message_intent,
    extracted_entities JSONB,
    rich_content JSONB,
    sent_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.message_sequence,
        m.message_type,
        m.message_text,
        m.is_from_user,
        m.detected_intent,
        m.extracted_entities,
        m.rich_content,
        m.sent_at
    FROM messages m
    WHERE m.conversation_id = p_conversation_id
        AND m.deleted_at IS NULL
    ORDER BY m.message_sequence DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Search knowledge base semantically (placeholder - requires vector extension)
CREATE OR REPLACE FUNCTION search_knowledge_base(
    p_query TEXT,
    p_language VARCHAR DEFAULT 'es',
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    document_id UUID,
    document_title VARCHAR,
    content TEXT,
    similarity_score NUMERIC
) AS $$
BEGIN
    -- This is a simplified full-text search
    -- In production, replace with vector similarity search using pgvector
    RETURN QUERY
    SELECT 
        id,
        ckd.document_title,
        ckd.content,
        ts_rank(search_vector, to_tsquery('spanish', p_query))::numeric AS similarity_score
    FROM chatbot_knowledge_documents ckd
    WHERE 
        ckd.language = p_language
        AND ckd.is_active = TRUE
        AND ckd.deleted_at IS NULL
        AND search_vector @@ to_tsquery('spanish', p_query)
    ORDER BY similarity_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Calculate chatbot response quality score
CREATE OR REPLACE FUNCTION calculate_message_quality_score(p_message_id UUID)
RETURNS NUMERIC AS $$
DECLARE
    v_score NUMERIC := 0;
    v_message RECORD;
BEGIN
    SELECT * INTO v_message FROM messages WHERE id = p_message_id;
    
    -- Confidence score (40%)
    v_score := v_score + (COALESCE(v_message.confidence_score, 0) * 0.40);
    
    -- User feedback (30%)
    IF v_message.user_feedback_helpful = TRUE THEN
        v_score := v_score + 0.30;
    ELSIF v_message.user_feedback_helpful = FALSE THEN
        v_score := v_score + 0;
    ELSE
        v_score := v_score + 0.15; -- Neutral if no feedback
    END IF;
    
    -- Interaction (20%)
    IF v_message.user_interacted = TRUE THEN
        v_score := v_score + 0.20;
    END IF;
    
    -- Verification status (10%)
    IF v_message.verified_by IS NOT NULL THEN
        v_score := v_score + 0.10;
    END IF;
    
    RETURN LEAST(v_score, 1.0);
END;
$$ LANGUAGE plpgsql;

-- Archive old conversations
CREATE OR REPLACE FUNCTION archive_old_conversations(p_days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    v_archived_count INTEGER;
BEGIN
    UPDATE conversations
    SET 
        conversation_status = 'ARCHIVED',
        archived_at = CURRENT_TIMESTAMP
    WHERE 
        last_message_at < CURRENT_TIMESTAMP - (p_days_old || ' days')::INTERVAL
        AND conversation_status = 'RESOLVED'
        AND archived_at IS NULL;
    
    GET DIAGNOSTICS v_archived_count = ROW_COUNT;
    RETURN v_archived_count;
END;
$$ LANGUAGE plpgsql;

-- Refresh chatbot analytics
CREATE OR REPLACE FUNCTION refresh_chatbot_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_chatbot_performance;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_knowledge_documents;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_common_intents;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INTEGRATION WITH EXISTING TABLES
-- ============================================================================

-- Link messages to plant views
CREATE OR REPLACE FUNCTION log_plant_view_from_chat()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.interaction_type = 'VIEWED_PLANT' AND NEW.interaction_metadata->>'plant_id' IS NOT NULL THEN
        INSERT INTO user_plant_views (
            user_id,
            plant_id,
            came_from_search,
            session_id,
            referrer_url
        ) VALUES (
            (SELECT user_id FROM conversations WHERE id = NEW.conversation_id),
            (NEW.interaction_metadata->>'plant_id')::UUID,
            TRUE,
            (SELECT session_id FROM conversations WHERE id = NEW.conversation_id),
            'chatbot'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_log_plant_view_from_chat
AFTER UPDATE ON messages
FOR EACH ROW
WHEN (NEW.user_interacted = TRUE AND OLD.user_interacted = FALSE)
EXECUTE FUNCTION log_plant_view_from_chat();

-- ============================================================================
-- CHATBOT PERMISSIONS
-- ============================================================================

-- Add chatbot-specific permissions (skipped - permissions table is in auth DB)
-- INSERT INTO permissions (resource_type, action, name, display_name, description) VALUES
-- ('CONVERSATION', 'READ', 'conversation.read', 'Ver conversaciones', 'Puede ver conversaciones de chatbot'),
-- ('CONVERSATION', 'CREATE', 'conversation.create', 'Iniciar conversaciones', 'Puede iniciar nuevas conversaciones'),
-- ('CONVERSATION', 'UPDATE', 'conversation.update', 'Editar conversaciones', 'Puede editar conversaciones'),
-- ('CONVERSATION', 'DELETE', 'conversation.delete', 'Eliminar conversaciones', 'Puede eliminar conversaciones'),
-- ('CONVERSATION', 'MODERATE', 'conversation.moderate', 'Moderar conversaciones', 'Puede revisar y moderar conversaciones')
-- -- ON CONFLICT (resource_type, action) DO NOTHING;

-- Grant chatbot permissions to roles
-- DO $$
-- DECLARE
--     v_client_role_id UUID;
--     v_researcher_role_id UUID;
--     v_moderator_role_id UUID;
-- BEGIN
--     SELECT id INTO v_client_role_id FROM roles WHERE name = 'CLIENT';
--     SELECT id INTO v_researcher_role_id FROM roles WHERE name = 'RESEARCHER';
--     SELECT id INTO v_moderator_role_id FROM roles WHERE name = 'MODERATOR';
--     
--     -- Clients can read and create their own conversations
--     INSERT INTO role_permissions (role_id, permission_id, is_granted, additional_conditions)
--     SELECT v_client_role_id, id, TRUE, '{"own_resource_only": true}'::jsonb
--     FROM permissions WHERE name IN ('conversation.read', 'conversation.create')
--     ON CONFLICT DO NOTHING;
--     
--     -- Researchers can moderate conversations
--     INSERT INTO role_permissions (role_id, permission_id, is_granted)
--     SELECT v_researcher_role_id, id, TRUE
--     FROM permissions WHERE name IN ('conversation.read', 'conversation.moderate')
--     ON CONFLICT DO NOTHING;
--     
--     -- Moderators get full conversation access
--     INSERT INTO role_permissions (role_id, permission_id, is_granted)
--     SELECT v_moderator_role_id, id, TRUE
--     FROM permissions WHERE name LIKE 'conversation.%'
--     ON CONFLICT DO NOTHING;
-- END $$;

-- ============================================================================
-- SAMPLE CHATBOT KNOWLEDGE BASE (for testing)
-- ============================================================================

INSERT INTO chatbot_knowledge_documents (document_title, document_type, content, language, tags, related_intents) VALUES
(
    'Manzanilla - Propiedades Medicinales',
    'plant_summary',
    'La manzanilla (Matricaria chamomilla) es una planta medicinal ampliamente utilizada en México para tratar problemas digestivos, ansiedad e inflamación. Se prepara principalmente en infusión.',
    'es',
    '["manzanilla", "digestión", "ansiedad"]'::jsonb,
    '["PLANT_SEARCH", "PREPARATION_QUESTION"]'::jsonb
),
(
    'Cómo preparar té medicinal',
    'preparation_guide',
    'Para preparar un té medicinal: 1) Hierve agua, 2) Agrega 1-2 cucharaditas de hierba seca por taza, 3) Deja reposar 5-10 minutos, 4) Cuela y bebe. No exceder 3 tazas al día.',
    'es',
    '["preparación", "té", "infusión"]'::jsonb,
    '["PREPARATION_QUESTION", "DOSAGE_QUESTION"]'::jsonb
),
(
    'Advertencias sobre uso de plantas medicinales',
    'safety_info',
    'Importante: Las plantas medicinales pueden tener efectos secundarios e interacciones con medicamentos. Consulta a un médico si: estás embarazada, amamantando, tomando medicamentos o tienes condiciones médicas crónicas.',
    'es',
    '["seguridad", "advertencias", "contraindicaciones"]'::jsonb,
    '["SIDE_EFFECTS_INQUIRY", "GENERAL_QUESTION"]'::jsonb
);

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

-- DO $$
-- BEGIN
--     RAISE NOTICE '================================================================';
--     RAISE NOTICE 'CHATBOT MODULE ADDED SUCCESSFULLY';
--     RAISE NOTICE '================================================================';
--     RAISE NOTICE 'New Tables: 11';
--     RAISE NOTICE 'New Materialized Views: 3';
--     RAISE NOTICE 'New Functions: 7';
--     RAISE NOTICE 'New Triggers: 4';
--     RAISE NOTICE '================================================================';
--     RAISE NOTICE 'Features:';
--     RAISE NOTICE '- Multi-turn conversation tracking';
--     RAISE NOTICE '- NLP intent detection & entity extraction';
--     RAISE NOTICE '- RAG knowledge base with semantic search';
--     RAISE NOTICE '- User feedback & quality scoring';
--     RAISE NOTICE '- Conversation analytics & patterns';
--     RAISE NOTICE '- Integration with plant views & favorites';
--     RAISE NOTICE '- Escalation to researchers';
--     RAISE NOTICE '- Quick replies & context management';
--     RAISE NOTICE '================================================================';
--     RAISE NOTICE 'Recommended Extensions:';
--     RAISE NOTICE '- pgvector: For semantic search (vector embeddings)';
--     RAISE NOTICE '- pg_partman: For message table partitioning at scale';
--     RAISE NOTICE '================================================================';
-- END $$;

