-- Core Database Schema
-- Sistema Inteligente de Análisis de Plantas Medicinales de México

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ============================================================================
-- TAXONOMIC AND PLANT DATA (Enhanced from v1.0)
-- ============================================================================

CREATE TABLE taxonomic_families (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scientific_name VARCHAR(255) NOT NULL UNIQUE,
    common_names JSONB DEFAULT '[]',
    description TEXT,
    
    -- Verification
    verification_status verification_status DEFAULT 'VERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_families_status ON taxonomic_families(verification_status) WHERE deleted_at IS NULL;

CREATE TABLE taxonomic_genera (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID REFERENCES taxonomic_families(id) ON DELETE CASCADE,
    scientific_name VARCHAR(255) NOT NULL UNIQUE,
    common_names JSONB DEFAULT '[]',
    description TEXT,
    
    -- Verification
    verification_status verification_status DEFAULT 'VERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_genera_family ON taxonomic_genera(family_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_genera_status ON taxonomic_genera(verification_status) WHERE deleted_at IS NULL;

-- Main plants table with versioning
CREATE TABLE plants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    genus_id UUID REFERENCES taxonomic_genera(id) ON DELETE CASCADE,
    
    -- Current version tracking
    current_version_id UUID, -- Self-reference to plant_versions
    version_number INTEGER DEFAULT 1,
    
    -- Taxonomic classification
    scientific_name VARCHAR(500) NOT NULL UNIQUE,
    species VARCHAR(255),
    subspecies VARCHAR(255),
    variety VARCHAR(255),
    
    -- Geographic distribution
    endemic_to_mexico BOOLEAN DEFAULT FALSE,
    mexican_states JSONB DEFAULT '[]', -- Array of state names
    distribution_map_url TEXT,
    
    -- Conservation
    conservation_status VARCHAR(100),
    iucn_status VARCHAR(50),
    is_endangered BOOLEAN DEFAULT FALSE,
    
    -- Verification workflow
    verification_status verification_status DEFAULT 'UNVERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Quality metrics
    data_completeness_score NUMERIC(3,2) CHECK (data_completeness_score BETWEEN 0 AND 1),
    scientific_evidence_score NUMERIC(3,2) CHECK (scientific_evidence_score BETWEEN 0 AND 1),
    user_trust_score NUMERIC(3,2) CHECK (user_trust_score BETWEEN 0 AND 1),
    
    -- Visibility
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- User engagement metrics (denormalized for performance)
    view_count BIGINT DEFAULT 0,
    favorite_count BIGINT DEFAULT 0,
    usage_report_count BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Full-text search
    search_vector tsvector
);

CREATE INDEX idx_plants_genus ON plants(genus_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_plants_verification ON plants(verification_status) WHERE deleted_at IS NULL;
CREATE INDEX idx_plants_published ON plants(is_published) WHERE deleted_at IS NULL;
CREATE INDEX idx_plants_endemic ON plants(endemic_to_mexico) WHERE deleted_at IS NULL;
CREATE INDEX idx_plants_states ON plants USING GIN(mexican_states) WHERE deleted_at IS NULL;
CREATE INDEX idx_plants_search ON plants USING GIN(search_vector) WHERE deleted_at IS NULL;
CREATE INDEX idx_plants_engagement ON plants(view_count DESC, favorite_count DESC) WHERE deleted_at IS NULL;

COMMENT ON TABLE plants IS 'Master plant records with versioning and verification workflow';

-- Plant versions (complete history)
CREATE TABLE plant_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Snapshot of all plant data at this version
    version_data JSONB NOT NULL,
    /* Stores complete plant state including:
    - All taxonomic data
    - Names and descriptions
    - Geographic data
    - References
    - Compounds and activities at this version
    */
    
    -- Change tracking
    changes_summary TEXT,
    changed_fields JSONB, -- Array of field names that changed
    
    -- Version metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    change_reason TEXT,
    
    -- Verification at version level
    verification_status verification_status,
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(plant_id, version_number)
);

CREATE INDEX idx_plant_versions_plant ON plant_versions(plant_id);
CREATE INDEX idx_plant_versions_created ON plant_versions(created_at DESC);

COMMENT ON TABLE plant_versions IS 'Complete version history for scientific reproducibility';

-- Add foreign key to plants table for current version
ALTER TABLE plants ADD CONSTRAINT fk_plants_current_version 
    FOREIGN KEY (current_version_id) REFERENCES plant_versions(id);

-- Plant names (normalized, multilingual)
CREATE TABLE plant_names (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    
    -- Name data
    name VARCHAR(500) NOT NULL,
    name_type VARCHAR(50) NOT NULL, -- 'scientific', 'common', 'indigenous', 'regional'
    language VARCHAR(10), -- ISO 639-1 code: 'es', 'en', 'nah', 'may', etc.
    region VARCHAR(100), -- State or region where this name is used
    
    -- Indigenous language context
    indigenous_language VARCHAR(100), -- e.g., 'Náhuatl', 'Maya', 'Zapoteco'
    cultural_group VARCHAR(100),
    
    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Source
    source TEXT,
    source_type data_source_type,
    
    -- Usage frequency (for ranking)
    usage_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_plant_names_plaplant_names(plant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_names_type ON plant_names(name_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_names_language ON plant_names(language) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_names_region ON plant_names(region) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_names_name_trgm ON plant_names USING gin(name gin_trgm_ops) WHERE deleted_at IS NULL;

COMMENT ON TABLE plant_names IS 'Multilingual and regional plant names with indigenous language support';

-- Verification workflow tracking
CREATE TABLE plant_verification_workflow (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    
    -- Workflow state
    from_status verification_status,
    to_status verification_status NOT NULL,
    
    -- Review details
    reviewer_id UUID REFERENCES users(id),
    review_notes TEXT,
    review_checklist JSONB, -- Structured review criteria
    
    -- Supporting evidence
    evidence_provided JSONB, -- References, citations, sources
    
    -- Decision
    decision VARCHAR(50), -- 'approved', 'rejected', 'needs_revision'
    rejection_reason TEXT,
    
    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_verification_plant ON plant_verification_workflow(plant_id);
CREATE INDEX idx_verification_reviewer ON plant_verification_workflow(reviewer_id);
CREATE INDEX idx_verification_status ON plant_verification_workflow(to_status, reviewed_at);

COMMENT ON TABLE plant_verification_workflow IS 'Audit trail for verification status changes';

-- ============================================================================
-- CHEMICAL COMPOUNDS (Enhanced)
-- ============================================================================

CREATE TABLE chemical_compounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Chemical identification
    compound_name VARCHAR(500) NOT NULL,
    iupac_name TEXT,
    synonyms JSONB DEFAULT '[]',
    
    -- Chemical identifiers
    cas_number VARCHAR(50) UNIQUE,
    pubchem_cid VARCHAR(50),
    chemspider_id VARCHAR(50),
    chebi_id VARCHAR(50),
    kegg_compound_id VARCHAR(50),
    inchi TEXT,
    inchikey VARCHAR(27) UNIQUE,
    smiles TEXT,
    
    -- Chemical properties
    molecular_formula VARCHAR(255),
    molecular_weight NUMERIC(10,4),
    exact_mass NUMERIC(15,6),
    
    -- Structure
    structure_2d TEXT,
    structure_3d TEXT,
    fingerprint BIT(1024),
    
    -- Classification
    compound_class VARCHAR(255),
    subclass VARCHAR(255),
    biosynthetic_origin VARCHAR(255),
    
    -- Pharmacological properties
    pharmacological_activities JSONB DEFAULT '[]',
    mechanisms_of_action JSONB DEFAULT '[]',
    bioavailability_data JSONB,
    
    -- Toxicity
    toxicity_level toxicity_level DEFAULT 'UNKNOWN',
    ld50_data JSONB,
    adverse_effects JSONB DEFAULT '[]',
    
    -- Verification
    verification_status verification_status DEFAULT 'UNVERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Full-text search
    search_vector tsvector
);

CREATE INDEX idx_compounds_search ON chemical_compounds USING GIN(search_vector) WHERE deleted_at IS NULL;
CREATE INDEX idx_compounds_pubchem ON chemical_compounds(pubchem_cid) WHERE deleted_at IS NULL;
CREATE INDEX idx_compounds_cas ON chemical_compounds(cas_number) WHERE deleted_at IS NULL;
CREATE INDEX idx_compounds_inchikey ON chemical_compounds(inchikey) WHERE deleted_at IS NULL;
CREATE INDEX idx_compounds_class ON chemical_compounds(compound_class) WHERE deleted_at IS NULL;
CREATE INDEX idx_compounds_verification ON chemical_compounds(verification_status) WHERE deleted_at IS NULL;

-- Plant-Compound associations
CREATE TABLE plant_compounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    compound_id UUID NOT NULL REFERENCES chemical_compounds(id) ON DELETE CASCADE,
    
    -- Occurrence data
    plant_part VARCHAR(100),
    concentration_range JSONB,
    
    -- Evidence and inference
    evidence_level evidence_level NOT NULL,
    inference_method compound_inference_method,
    confidence_score NUMERIC(5,4) CHECK (confidence_score BETWEEN 0 AND 1),
    
    -- Inference details
    inference_details JSONB,
    
    -- Verification
    verification_status verification_status DEFAULT 'UNVERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Source attribution
    source_references JSONB, -- Array of article IDs or URLs
    
    -- User contribution tracking
    contributed_by UUID REFERENCES users(id),
    contribution_date TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(plant_id, compound_id, plant_part)
);

CREATE INDEX idx_plant_compounds_plant ON plant_compounds(plant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_compounds_compound ON plant_compounds(compound_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_compounds_evidence ON plant_compounds(evidence_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_compounds_confidence ON plant_compounds(confidence_score DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_compounds_verification ON plant_compounds(verification_status) WHERE deleted_at IS NULL;

-- ============================================================================
-- MEDICINAL ACTIVITIES
-- ============================================================================

CREATE TABLE medicinal_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Activity identification
    activity_name VARCHAR(500) NOT NULL UNIQUE,
    synonyms JSONB DEFAULT '[]',
    description TEXT,
    
    -- Classification
    category VARCHAR(255), -- 'antimicrobial', 'anti-inflammatory', 'analgesic', etc.
    subcategory VARCHAR(255),
    
    -- Medical ontology mapping
    mesh_id VARCHAR(50),
    snomed_ct_id VARCHAR(50),
    
    -- Related medical conditions
    related_conditions JSONB, -- Array of condition IDs or names
    
    -- Mechanism overview
    mechanism_summary TEXT,
    
    -- Verification
    verification_status verification_status DEFAULT 'VERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    search_vector tsvector
);

CREATE INDEX idx_activities_search ON medicinal_activities USING GIN(search_vector) WHERE deleted_at IS NULL;
CREATE INDEX idx_activities_category ON medicinal_activities(category) WHERE deleted_at IS NULL;

CREATE TABLE plant_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES medicinal_activities(id) ON DELETE CASCADE,
    
    -- Activity details
    plant_part VARCHAR(100),
    preparation_method preparation_method,
    
    -- Evidence
    evidence_level evidence_level NOT NULL,
    confidence_score NUMERIC(5,4) CHECK (confidence_score BETWEEN 0 AND 1),
    
    -- Verification status
    verification_status verification_status DEFAULT 'UNVERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Supporting evidence
    supporting_compounds JSONB, -- Array of compound IDs
    source_references JSONB, -- Array of article IDs
    
    -- Traditional use context
    traditional_use_description TEXT,
    traditional_preparation TEXT,
    geographic_usage JSONB,
    
    -- User contribution
    contributed_by UUID REFERENCES users(id),
    contribution_date TIMESTAMP WITH TIME ZONE,
    
    -- Efficacy data from user reports (aggregated)
    user_effectiveness_avg NUMERIC(3,2),
    user_report_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(plant_id, activity_id, plant_part, preparation_method)
);

CREATE INDEX idx_plant_activities_plant ON plant_activities(plant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_activities_activity ON plant_activities(activity_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_activities_evidence ON plant_activities(evidence_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_activities_verification ON plant_activities(verification_status) WHERE deleted_at IS NULL;
CREATE INDEX idx_plant_activities_effectiveness ON plant_activities(user_effectiveness_avg DESC NULLS LAST) WHERE deleted_at IS NULL;

COMMENT ON TABLE plant_activities IS 'Medicinal activities with verification workflow and user effectiveness data';

-- Research gaps (activities reported but lacking scientific validation)
CREATE TABLE research_gaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES medicinal_activities(id) ON DELETE SET NULL,
    
    -- Gap description
    gap_type VARCHAR(100), -- 'missing_compound_data', 'lacking_clinical_trial', 'unverified_activity', etc.
    description TEXT NOT NULL,
    
    -- Evidence of gap
    user_report_count INTEGER DEFAULT 0, -- How many users reported this
    traditional_use_evidence TEXT,
    
    -- Priority
    priority_level INTEGER CHECK (priority_level BETWEEN 1 AND 5), -- 5 = highest
    
    -- Research proposal
    proposed_research TEXT,
    estimated_effort VARCHAR(50), -- 'low', 'medium', 'high'
    
    -- Status
    status VARCHAR(50) DEFAULT 'identified', -- 'identified', 'under_investigation', 'resolved', 'dismissed'
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    
    -- Metadata
    identified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    identified_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_research_gaps_plant ON research_gaps(plant_id);
CREATE INDEX idx_research_gaps_status ON research_gaps(status);
CREATE INDEX idx_research_gaps_priority ON research_gaps(priority_level DESC);

COMMENT ON TABLE research_gaps IS 'Identified knowledge gaps requiring scientific investigation';

-- ============================================================================
-- SCIENTIFIC LITERATURE
-- ============================================================================

CREATE TABLE scientific_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Article identification
    title TEXT NOT NULL,
    abstract TEXT,
    
    -- Publication identifiers
    doi VARCHAR(255) UNIQUE,
    pubmed_id VARCHAR(50) UNIQUE,
    pmcid VARCHAR(50),
    arxiv_id VARCHAR(50),
    
    -- Publication details
    journal VARCHAR(500),
    publication_date DATE,
    volume VARCHAR(50),
    issue VARCHAR(50),
    pages VARCHAR(50),
    
    -- Authors
    authors JSONB NOT NULL,
    
    -- Content
    keywords JSONB DEFAULT '[]',
    mesh_terms JSONB DEFAULT '[]',
    
    -- Access
    is_open_access BOOLEAN DEFAULT FALSE,
    pdf_url TEXT,
    full_text_url TEXT,
    full_text TEXT,
    
    -- Metrics
    citation_count INTEGER DEFAULT 0,
    impact_factor NUMERIC(6,3),
    
    -- Article type
    article_type VARCHAR(100),
    
    -- Quality assessment
    quality_score NUMERIC(3,2) CHECK (quality_score BETWEEN 0 AND 1),
    peer_reviewed BOOLEAN DEFAULT TRUE,
    
    -- User contribution
    uploaded_by UUID REFERENCES users(id),
    upload_notes TEXT,
    
    -- Verification
    verification_status verification_status DEFAULT 'UNVERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_fetched TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    search_vector tsvector
);

CREATE INDEX idx_articles_search ON scientific_articles USING GIN(search_vector) WHERE deleted_at IS NULL;
CREATE INDEX idx_articles_doi ON scientific_articles(doi) WHERE deleted_at IS NULL;
CREATE INDEX idx_articles_pubmed ON scientific_articles(pubmed_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_articles_date ON scientific_articles(publication_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_articles_quality ON scientific_articles(quality_score DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_articles_uploaded ON scientific_articles(uploaded_by) WHERE deleted_at IS NULL;

CREATE TABLE article_plant_associations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES scientific_articles(id) ON DELETE CASCADE,
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    
    -- Relevance
    relevance_score NUMERIC(3,2) CHECK (relevance_score BETWEEN 0 AND 1),
    mentioned_in_abstract BOOLEAN DEFAULT FALSE,
    mentioned_in_title BOOLEAN DEFAULT FALSE,
    
    -- Extracted data
    key_findings TEXT,
    extracted_data JSONB,
    
    -- Created by researcher or automated
    created_by UUID REFERENCES users(id),
    is_automated BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(article_id, plant_id)
);

CREATE INDEX idx_article_plant_article ON article_plant_associations(article_id);
CREATE INDEX idx_article_plant_plant ON article_plant_associations(plant_id);
CREATE INDEX idx_article_plant_relevance ON article_plant_associations(relevance_score DESC);

CREATE TABLE article_compound_associations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES scientific_articles(id) ON DELETE CASCADE,
    compound_id UUID NOT NULL REFERENCES chemical_compounds(id) ON DELETE CASCADE,
    
    -- Context
    relevance_score NUMERIC(3,2) CHECK (relevance_score BETWEEN 0 AND 1),
    key_findings TEXT,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(article_id, compound_id)
);

CREATE INDEX idx_article_compound_article ON article_compound_associations(article_id);
CREATE INDEX idx_article_compound_compound ON article_compound_associations(compound_id);



-- ============================================================================
-- API CACHE & DATA SOURCES
-- ============================================================================

CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(255) NOT NULL UNIQUE,
    source_type data_source_type NOT NULL,
    
    -- Source details
    base_url TEXT,
    api_version VARCHAR(50),
    documentation_url TEXT,
    
    -- Access
    requires_authentication BOOLEAN DEFAULT FALSE,
    credential_reference VARCHAR(255),
    
    -- Rate limiting
    rate_limit_per_hour INTEGER,
    rate_limit_per_day INTEGER,
    current_hour_usage INTEGER DEFAULT 0,
    current_day_usage INTEGER DEFAULT 0,
    last_reset_hour TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_reset_day TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Quality metrics
    reliability_score NUMERIC(3,2) CHECK (reliability_score BETWEEN 0 AND 1),
    last_successful_access TIMESTAMP WITH TIME ZONE,
    last_failed_access TIMESTAMP WITH TIME ZONE,
    consecutive_failures INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_sources_type ON data_sources(source_type) WHERE is_active = TRUE;

CREATE TABLE api_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Cache key
    source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    endpoint VARCHAR(500) NOT NULL,
    query_parameters JSONB,
    cache_key VARCHAR(64) GENERATED ALWAYS AS (
        md5(source_id::text || endpoint || COALESCE(query_parameters::text, ''))
    ) STORED UNIQUE,
    
    -- Cached response
    response_data JSONB NOT NULL,
    response_metadata JSONB,
    
    -- Cache management
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    
    -- Quality
    is_error BOOLEAN DEFAULT FALSE,
    error_details TEXT,
    http_status_code INTEGER
);

CREATE INDEX idx_cache_key ON api_cache(cache_key);
CREATE INDEX idx_cache_source ON api_cache(source_id);
CREATE INDEX idx_cache_expires ON api_cache(expires_at);



-- ============================================================================
-- GENOMIC DATA (from v1.0, enhanced)
-- ============================================================================

CREATE TABLE genomic_sequences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    
    -- Sequence identification
    genbank_accession VARCHAR(50) UNIQUE,
    sequence_type VARCHAR(100),
    gene_name VARCHAR(255),
    
    -- Sequence data
    fasta_sequence TEXT NOT NULL,
    sequence_length INTEGER,
    gc_content NUMERIC(5,2),
    
    -- Annotations
    coding_regions JSONB,
    functional_annotation TEXT,
    pathway_associations JSONB,
    
    -- Quality
    sequencing_method VARCHAR(255),
    quality_score NUMERIC(5,2),
    coverage NUMERIC(10,2),
    
    -- Source
    source_database data_source_type DEFAULT 'NCBI',
    external_id VARCHAR(255),
    source_url TEXT,
    
    -- User contribution
    uploaded_by UUID REFERENCES users(id),
    
    -- Verification
    verification_status verification_status DEFAULT 'UNVERIFIED',
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_genomic_plant ON genomic_sequences(plant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_genomic_accession ON genomic_sequences(genbank_accession) WHERE deleted_at IS NULL;
CREATE INDEX idx_genomic_gene ON genomic_sequences(gene_name) WHERE deleted_at IS NULL;

CREATE TABLE blast_alignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_sequence_id UUID NOT NULL REFERENCES genomic_sequences(id) ON DELETE CASCADE,
    subject_sequence_id UUID NOT NULL REFERENCES genomic_sequences(id) ON DELETE CASCADE,
    
    -- Alignment metrics
    identity_percentage NUMERIC(5,2) NOT NULL,
    alignment_length INTEGER NOT NULL,
    mismatches INTEGER,
    gap_opens INTEGER,
    e_value DOUBLE PRECISION,
    bit_score NUMERIC(10,2),
    
    -- Alignment coordinates
    query_start INTEGER,
    query_end INTEGER,
    subject_start INTEGER,
    subject_end INTEGER,
    
    -- Analysis metadata
    blast_version VARCHAR(50),
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    parameters JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_blast_query ON blast_alignments(query_sequence_id);
CREATE INDEX idx_blast_subject ON blast_alignments(subject_sequence_id);
CREATE INDEX idx_blast_identity ON blast_alignments(identity_percentage DESC);

-- ============================================================================
-- PROBABILITY WEIGHTS & ANALYTICS
-- ============================================================================

CREATE TABLE probability_weight_schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    
    -- Weight configuration
    weights JSONB NOT NULL,
    
    -- Versioning
    version VARCHAR(50) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default schema
INSERT INTO probability_weight_schemas (schema_name, description, weights, created_by) VALUES
('default_v1', 'Default probability calculation weights', 
'{
    "evidence_weights": {
        "LEVEL_1_PEER_REVIEWED": 1.0,
        "LEVEL_2_PHYTOCHEMICAL_DB": 0.85,
        "LEVEL_3_ETHNOBOTANICAL": 0.60,
        "LEVEL_4_GENOMIC_INFERENCE": 0.40,
        "LEVEL_5_USER_REPORTED": 0.30
    },
    "inference_method_weights": {
        "DIRECT_LITERATURE": 1.0,
        "GENE_CLUSTER_SIMILARITY": 0.75,
        "ENZYME_HOMOLOGY": 0.70,
        "PATHWAY_RECONSTRUCTION": 0.65,
        "BLAST_ALIGNMENT": 0.60,
        "MOLECULAR_SIMILARITY": 0.55,
        "USER_REPORTED": 0.25
    },
    "user_effectiveness_weight": 0.20,
    "regional_relevance_weight": 0.15
}'::jsonb, NULL);

-- ============================================================================
-- REDIS COORDINATION


-- ============================================================================
-- REDIS COORDINATION
-- ============================================================================

CREATE TABLE redis_cache_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key_pattern VARCHAR(500) NOT NULL UNIQUE,
    description TEXT,
    default_ttl_seconds INTEGER,
    
    -- Statistics
    total_sets BIGINT DEFAULT 0,
    total_gets BIGINT DEFAULT 0,
    cache_hits BIGINT DEFAULT 0,
    cache_misses BIGINT DEFAULT 0,
    hit_rate NUMERIC(5,4) GENERATED ALWAYS AS (
        CASE WHEN total_gets > 0 
        THEN cache_hits::numeric / total_gets::numeric 
        ELSE 0 END
    ) STORED,
    
    last_set_at TIMESTAMP WITH TIME ZONE,
    last_get_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MATERIALIZED VIEWS FOR ANALYTICS


-- ============================================================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================================================

-- Most searched plants
CREATE MATERIALIZED VIEW mv_most_searched_plants AS
SELECT 
    p.id,
    p.scientific_name,
    COUNT(DISTINCT ush.id) AS search_count,
    COUNT(DISTINCT ush.user_id) AS unique_searchers,
    COUNT(DISTINCT CASE WHEN ush.clicked_result_id IS NOT NULL THEN ush.id END) AS click_count,
    ROUND(
        COUNT(DISTINCT CASE WHEN ush.clicked_result_id IS NOT NULL THEN ush.id END)::numeric / 
        NULLIF(COUNT(DISTINCT ush.id), 0) * 100, 
        2
    ) AS click_through_rate,
    MAX(ush.searched_at) AS last_searched_at
FROM plants p
LEFT JOIN user_search_history ush ON p.id = ush.clicked_result_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.scientific_name
ORDER BY search_count DESC;

CREATE UNIQUE INDEX ON mv_most_searched_plants (id);

-- Most viewed plants
CREATE MATERIALIZED VIEW mv_most_viewed_plants AS
SELECT 
    p.id,
    p.scientific_name,
    COUNT(DISTINCT upv.id) AS view_count,
    COUNT(DISTINCT upv.user_id) FILTER (WHERE upv.user_id IS NOT NULL) AS unique_viewers,
    ROUND(AVG(EXTRACT(EPOCH FROM upv.view_duration)), 2) AS avg_view_duration_seconds,
    ROUND(AVG(upv.depth_score), 3) AS avg_depth_score,
    MAX(upv.viewed_at) AS last_viewed_at
FROM plants p
LEFT JOIN user_plant_views upv ON p.id = upv.plant_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.scientific_name
ORDER BY view_count DESC;

CREATE UNIQUE INDEX ON mv_most_viewed_plants (id);

-- Most favorited plants
CREATE MATERIALIZED VIEW mv_most_favorited_plants AS
SELECT 
    p.id,
    p.scientific_name,
    COUNT(DISTINCT upf.user_id) AS favorite_count,
    MAX(upf.favorited_at) AS last_favorited_at
FROM plants p
LEFT JOIN user_plant_favorites upf ON p.id = upf.plant_id AND upf.is_active = TRUE
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.scientific_name
ORDER BY favorite_count DESC;

CREATE UNIQUE INDEX ON mv_most_favorited_plants (id);

-- Most used plants (with effectiveness)
CREATE MATERIALIZED VIEW mv_most_used_plants AS
SELECT 
    p.id,
    p.scientific_name,
    COUNT(DISTINCT upur.id) AS usage_report_count,
    COUNT(DISTINCT upur.user_id) AS unique_users,
    ROUND(AVG(
        CASE upur.effectiveness_rating
            WHEN 'HIGHLY_EFFECTIVE' THEN 5
            WHEN 'MODERATELY_EFFECTIVE' THEN 4
            WHEN 'SLIGHTLY_EFFECTIVE' THEN 3
            WHEN 'NOT_EFFECTIVE' THEN 2
            WHEN 'UNSURE' THEN NULL
            WHEN 'ADVERSE_REACTION' THEN 1
        END
    ), 2) AS avg_effectiveness_score,
    COUNT(DISTINCT CASE WHEN upur.effectiveness_rating IN ('HIGHLY_EFFECTIVE', 'MODERATELY_EFFECTIVE') 
        THEN upur.id END) AS positive_report_count,
    COUNT(DISTINCT CASE WHEN upur.side_effects_observed = TRUE 
        THEN upur.id END) AS side_effect_report_count,
    MAX(upur.reported_at) AS last_reported_at
FROM plants p
LEFT JOIN user_plant_usage_reports upur ON p.id = upur.plant_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.scientific_name
ORDER BY usage_report_count DESC;

CREATE UNIQUE INDEX ON mv_most_used_plants (id);

-- Plants with high effectiveness but low scientific evidence
CREATE MATERIALIZED VIEW mv_high_effectiveness_low_evidence AS
SELECT 
    p.id,
    p.scientific_name,
    p.verification_status,
    p.scientific_evidence_score,
    COUNT(DISTINCT pc.id) FILTER (WHERE pc.evidence_level = 'LEVEL_1_PEER_REVIEWED') AS peer_reviewed_compound_count,
    COUNT(DISTINCT pa.id) FILTER (WHERE pa.evidence_level = 'LEVEL_1_PEER_REVIEWED') AS peer_reviewed_activity_count,
    COUNT(DISTINCT upur.id) AS usage_report_count,
    ROUND(AVG(
        CASE upur.effectiveness_rating
            WHEN 'HIGHLY_EFFECTIVE' THEN 5
            WHEN 'MODERATELY_EFFECTIVE' THEN 4
            WHEN 'SLIGHTLY_EFFECTIVE' THEN 3
            ELSE 2
        END
    ), 2) AS avg_effectiveness_score
FROM plants p
LEFT JOIN plant_compounds pc ON p.id = pc.plant_id AND pc.deleted_at IS NULL
LEFT JOIN plant_activities pa ON p.id = pa.plant_id AND pa.deleted_at IS NULL
LEFT JOIN user_plant_usage_reports upur ON p.id = upur.plant_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.scientific_name, p.verification_status, p.scientific_evidence_score
HAVING 
    COUNT(DISTINCT upur.id) >= 10  -- At least 10 user reports
    AND AVG(CASE upur.effectiveness_rating
        WHEN 'HIGHLY_EFFECTIVE' THEN 5
        WHEN 'MODERATELY_EFFECTIVE' THEN 4
        WHEN 'SLIGHTLY_EFFECTIVE' THEN 3
        ELSE 2
    END) >= 3.5  -- Average effectiveness >= 3.5
    AND (
        COUNT(DISTINCT pc.id) FILTER (WHERE pc.evidence_level = 'LEVEL_1_PEER_REVIEWED') < 3
        OR COUNT(DISTINCT pa.id) FILTER (WHERE pa.evidence_level = 'LEVEL_1_PEER_REVIEWED') < 3
    )
ORDER BY avg_effectiveness_score DESC, usage_report_count DESC;

CREATE UNIQUE INDEX ON mv_high_effectiveness_low_evidence (id);

COMMENT ON MATERIALIZED VIEW mv_high_effectiveness_low_evidence IS 'Research priority: plants with high user-reported effectiveness but lacking peer-reviewed evidence';

-- Regional usage trends
CREATE MATERIALIZED VIEW mv_regional_usage_trends AS
SELECT 
    p.id AS plant_id,
    p.scientific_name,
    upur.user_location->>'state' AS state,
    COUNT(DISTINCT upur.id) AS usage_count,
    COUNT(DISTINCT upur.user_id) AS unique_users,
    ROUND(AVG(
        CASE upur.effectiveness_rating
            WHEN 'HIGHLY_EFFECTIVE' THEN 5
            WHEN 'MODERATELY_EFFECTIVE' THEN 4
            WHEN 'SLIGHTLY_EFFECTIVE' THEN 3
            ELSE 2
        END
    ), 2) AS avg_effectiveness_score,
    jsonb_agg(DISTINCT upur.condition_treated) FILTER (WHERE upur.condition_treated IS NOT NULL) AS common_conditions
FROM plants p
INNER JOIN user_plant_usage_reports upur ON p.id = upur.plant_id
WHERE p.deleted_at IS NULL
    AND upur.user_location->>'state' IS NOT NULL
GROUP BY p.id, p.scientific_name, upur.user_location->>'state'
HAVING COUNT(DISTINCT upur.id) >= 3  -- At least 3 reports per region
ORDER BY state, usage_count DESC;

CREATE INDEX ON mv_regional_usage_trends (state);
CREATE INDEX ON mv_regional_usage_trends (plant_id);

-- Sponsor performance
CREATE MATERIALIZED VIEW mv_sponsor_performance AS
SELECT 
    s.id AS sponsor_id,
    s.company_name,
    COUNT(DISTINCT sp.plant_id) AS sponsored_plant_count,
    COUNT(DISTINCT sc.compound_id) AS sponsored_compound_count,
    SUM(sp.impression_count) AS total_impressions,
    SUM(sp.click_count) AS total_clicks,
    SUM(sp.conversion_count) AS total_conversions,
    ROUND(
        CASE WHEN SUM(sp.impression_count) > 0 
        THEN (SUM(sp.click_count)::numeric / SUM(sp.impression_count)) * 100 
        ELSE 0 END, 
        2
    ) AS click_through_rate,
    ROUND(
        CASE WHEN SUM(sp.click_count) > 0 
        THEN (SUM(sp.conversion_count)::numeric / SUM(sp.click_count)) * 100 
        ELSE 0 END, 
        2
    ) AS conversion_rate,
    SUM(sp.spent_to_date) AS total_spent,
    ROUND(
        CASE WHEN SUM(sp.conversion_count) > 0 
        THEN SUM(sp.spent_to_date) / SUM(sp.conversion_count) 
        ELSE 0 END, 
        2
    ) AS cost_per_conversion
FROM sponsors s
LEFT JOIN sponsored_plants sp ON s.id = sp.sponsor_id AND sp.is_active = TRUE
LEFT JOIN sponsored_compounds sc ON s.id = sc.sponsor_id AND sc.is_active = TRUE
WHERE s.deleted_at IS NULL AND s.is_active = TRUE
GROUP BY s.id, s.company_name
ORDER BY total_conversions DESC;

CREATE UNIQUE INDEX ON mv_sponsor_performance (sponsor_id);

-- ============================================================================
-- FUNCTIONS AND PROCEDURES
