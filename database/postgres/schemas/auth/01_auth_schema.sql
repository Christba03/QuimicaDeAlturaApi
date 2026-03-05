-- Auth Database Schema
-- Sistema Inteligente de Análisis de Plantas Medicinales de México

-- ============================================================================
-- SISTEMA INTELIGENTE DE ANÁLISIS DE PLANTAS MEDICINALES DE MÉXICO
-- Production-Grade Database Schema v2.0
-- PostgreSQL 14+ Required
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "cube";
CREATE EXTENSION IF NOT EXISTS "earthdistance";
CREATE EXTENSION IF NOT EXISTS "citext"; -- Case-insensitive text

-- ============================================================================
-- DOMAIN TYPES AND ENUMS
-- ============================================================================

-- Evidence hierarchy
CREATE TYPE evidence_level AS ENUM (
    'LEVEL_1_PEER_REVIEWED',
    'LEVEL_2_PHYTOCHEMICAL_DB',
    'LEVEL_3_ETHNOBOTANICAL',
    'LEVEL_4_GENOMIC_INFERENCE',
    'LEVEL_5_USER_REPORTED'
);

-- Data sources
CREATE TYPE data_source_type AS ENUM (
    'PUBMED',
    'DOI',
    'KEGG',
    'NCBI',
    'BLAST',
    'CHEBI',
    'CHEMSPIDER',
    'PUBCHEM',
    'CONABIO',
    'ETHNOBOTANICAL_RECORD',
    'USER_CONTRIBUTION',
    'MANUAL_ENTRY',
    'WEB_SCRAPING',
    'RESEARCHER_UPLOAD'
);

-- Compound inference methods
CREATE TYPE compound_inference_method AS ENUM (
    'DIRECT_LITERATURE',
    'GENE_CLUSTER_SIMILARITY',
    'ENZYME_HOMOLOGY',
    'PATHWAY_RECONSTRUCTION',
    'FASTA_ALIGNMENT',
    'BLAST_ALIGNMENT',
    'MOLECULAR_SIMILARITY',
    'USER_REPORTED'
);

-- Preparation methods
CREATE TYPE preparation_method AS ENUM (
    'INFUSION',
    'DECOCTION',
    'TINCTURE',
    'POULTICE',
    'ESSENTIAL_OIL',
    'POWDER',
    'FRESH',
    'EXTRACT',
    'CAPSULE',
    'TEA',
    'JUICE',
    'PASTE',
    'OTHER'
);

-- Toxicity levels
CREATE TYPE toxicity_level AS ENUM (
    'NONE',
    'LOW',
    'MODERATE',
    'HIGH',
    'SEVERE',
    'UNKNOWN'
);

-- Verification status
CREATE TYPE verification_status AS ENUM (
    'UNVERIFIED',
    'UNDER_REVIEW',
    'VERIFIED',
    'REJECTED',
    'NEEDS_MORE_DATA',
    'CONFLICTING_DATA'
);

-- User roles
CREATE TYPE user_role AS ENUM (
    'CLIENT',
    'RESEARCHER',
    'CODER_MAINTAINER',
    'ADMIN',
    'MODERATOR'
);

-- Permission actions
CREATE TYPE permission_action AS ENUM (
    'CREATE',
    'READ',
    'UPDATE',
    'DELETE',
    'VERIFY',
    'APPROVE',
    'REJECT',
    'MODERATE',
    'EXPORT',
    'ADMIN'
);

-- Resource types
CREATE TYPE resource_type AS ENUM (
    'PLANT',
    'COMPOUND',
    'ARTICLE',
    'USER',
    'COMMENT',
    'REPORT',
    'SPONSOR',
    'SYSTEM_CONFIG'
);

-- Effectiveness ratings
CREATE TYPE effectiveness_rating AS ENUM (
    'HIGHLY_EFFECTIVE',
    'MODERATELY_EFFECTIVE',
    'SLIGHTLY_EFFECTIVE',
    'NOT_EFFECTIVE',
    'UNSURE',
    'ADVERSE_REACTION'
);

-- Side effect severity
CREATE TYPE severity_level AS ENUM (
    'MILD',
    'MODERATE',
    'SEVERE',
    'LIFE_THREATENING'
);

-- Recommendation types
CREATE TYPE recommendation_type AS ENUM (
    'ORGANIC',
    'SPONSORED',
    'HYBRID'
);

-- ============================================================================
-- USERS & ACCESS CONTROL
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Authentication
    email CITEXT NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    email_verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Profile
    username VARCHAR(50) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    profile_image_url TEXT,
    bio TEXT,
    
    -- Location (for regional recommendations)
    country VARCHAR(100) DEFAULT 'Mexico',
    state VARCHAR(100),
    city VARCHAR(100),
    latitude NUMERIC(10,8),
    longitude NUMERIC(11,8),
    
    -- Preferences
    preferred_language VARCHAR(10) DEFAULT 'es',
    timezone VARCHAR(50) DEFAULT 'America/Mexico_City',
    notification_preferences JSONB DEFAULT '{"email": true, "push": false}',
    
    -- Status
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    banned_at TIMESTAMP WITH TIME ZONE,
    banned_by UUID REFERENCES users(id),
    
    -- Security
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    
    -- Constraints
    CONSTRAINT valid_coordinates CHECK (
        (latitude IS NULL AND longitude IS NULL) OR
        (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
    )
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_location ON users(state, city) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_active ON users(is_banned) WHERE deleted_at IS NULL;

COMMENT ON TABLE users IS 'Core user accounts with authentication and profile data';
COMMENT ON COLUMN users.deleted_at IS 'Soft delete timestamp - NULL means active';

-- ============================================================================
-- ROLES & PERMISSIONS
-- ============================================================================

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name user_role NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Hierarchy
    parent_role_id UUID REFERENCES roles(id),
    hierarchy_level INTEGER NOT NULL,
    
    -- Status
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_roles_hierarchy ON roles(hierarchy_level);

COMMENT ON TABLE roles IS 'Role definitions with hierarchical structure';

-- Insert default roles
INSERT INTO roles (name, display_name, description, hierarchy_level) VALUES
('CLIENT', 'Cliente', 'Usuario final que busca y consulta información sobre plantas medicinales', 1),
('RESEARCHER', 'Investigador', 'Investigador que puede agregar y verificar datos científicos', 2),
('MODERATOR', 'Moderador', 'Usuario que puede moderar contenido y comentarios', 3),
('CODER_MAINTAINER', 'Desarrollador/Mantenedor', 'Desarrollador con acceso a configuración del sistema', 4),
('ADMIN', 'Administrador', 'Acceso completo al sistema', 5);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_type resource_type NOT NULL,
    action permission_action NOT NULL,
    
    -- Permission details
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(150) NOT NULL,
    description TEXT,
    
    -- Conditions (JSONB for flexible rule definitions)
    conditions JSONB DEFAULT '{}',
    /* Example:
    {
        "own_resource_only": true,
        "region_restricted": ["Oaxaca", "Chiapas"],
        "requires_verification": true
    }
    */
    
    -- Status
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    UNIQUE(resource_type, action)
);

CREATE INDEX idx_permissions_resource_action ON permissions(resource_type, action);

COMMENT ON TABLE permissions IS 'Granular permission definitions for role-based access control';

-- Insert default permissions
INSERT INTO permissions (resource_type, action, name, display_name, description) VALUES
-- Plant permissions
('PLANT', 'READ', 'plant.read', 'Ver plantas', 'Puede ver información de plantas'),
('PLANT', 'CREATE', 'plant.create', 'Crear plantas', 'Puede crear nuevos registros de plantas'),
('PLANT', 'UPDATE', 'plant.update', 'Editar plantas', 'Puede editar información de plantas'),
('PLANT', 'DELETE', 'plant.delete', 'Eliminar plantas', 'Puede eliminar registros de plantas'),
('PLANT', 'VERIFY', 'plant.verify', 'Verificar plantas', 'Puede verificar datos de plantas'),

-- Compound permissions
('COMPOUND', 'READ', 'compound.read', 'Ver compuestos', 'Puede ver información de compuestos'),
('COMPOUND', 'CREATE', 'compound.create', 'Crear compuestos', 'Puede crear registros de compuestos'),
('COMPOUND', 'UPDATE', 'compound.update', 'Editar compuestos', 'Puede editar compuestos'),
('COMPOUND', 'VERIFY', 'compound.verify', 'Verificar compuestos', 'Puede verificar datos de compuestos'),

-- Article permissions
('ARTICLE', 'READ', 'article.read', 'Ver artículos', 'Puede ver artículos científicos'),
('ARTICLE', 'CREATE', 'article.create', 'Agregar artículos', 'Puede agregar referencias científicas'),
('ARTICLE', 'UPDATE', 'article.update', 'Editar artículos', 'Puede editar referencias'),

-- Comment permissions
('COMMENT', 'READ', 'comment.read', 'Ver comentarios', 'Puede ver comentarios'),
('COMMENT', 'CREATE', 'comment.create', 'Crear comentarios', 'Puede crear comentarios'),
('COMMENT', 'UPDATE', 'comment.update', 'Editar comentarios', 'Puede editar sus comentarios'),
('COMMENT', 'DELETE', 'comment.delete', 'Eliminar comentarios', 'Puede eliminar comentarios'),
('COMMENT', 'MODERATE', 'comment.moderate', 'Moderar comentarios', 'Puede moderar comentarios de otros'),

-- Report permissions
('REPORT', 'CREATE', 'report.create', 'Crear reportes', 'Puede reportar uso de plantas'),
('REPORT', 'READ', 'report.read', 'Ver reportes', 'Puede ver reportes de usuarios'),

-- User permissions
('USER', 'READ', 'user.read', 'Ver usuarios', 'Puede ver perfiles de usuarios'),
('USER', 'UPDATE', 'user.update', 'Editar usuarios', 'Puede editar usuarios'),
('USER', 'DELETE', 'user.delete', 'Eliminar usuarios', 'Puede eliminar usuarios'),
('USER', 'ADMIN', 'user.admin', 'Administrar usuarios', 'Administración completa de usuarios'),

-- System permissions
('SYSTEM_CONFIG', 'READ', 'system.read', 'Ver configuración', 'Puede ver configuración del sistema'),
('SYSTEM_CONFIG', 'UPDATE', 'system.update', 'Editar configuración', 'Puede modificar configuración'),
('SYSTEM_CONFIG', 'ADMIN', 'system.admin', 'Administrar sistema', 'Acceso completo al sistema');

CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    
    -- Permission can be granted or denied
    is_granted BOOLEAN DEFAULT TRUE,
    
    -- Additional conditions specific to this role-permission
    additional_conditions JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID REFERENCES users(id),
    
    UNIQUE(role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);

-- Assign default permissions to roles
DO $$
DECLARE
    v_client_role_id UUID;
    v_researcher_role_id UUID;
    v_moderator_role_id UUID;
    v_coder_role_id UUID;
    v_admin_role_id UUID;
BEGIN
    -- Get role IDs
    SELECT id INTO v_client_role_id FROM roles WHERE name = 'CLIENT';
    SELECT id INTO v_researcher_role_id FROM roles WHERE name = 'RESEARCHER';
    SELECT id INTO v_moderator_role_id FROM roles WHERE name = 'MODERATOR';
    SELECT id INTO v_coder_role_id FROM roles WHERE name = 'CODER_MAINTAINER';
    SELECT id INTO v_admin_role_id FROM roles WHERE name = 'ADMIN';
    
    -- CLIENT permissions
    INSERT INTO role_permissions (role_id, permission_id, is_granted)
    SELECT v_client_role_id, id, TRUE FROM permissions WHERE name IN (
        'plant.read', 'compound.read', 'article.read',
        'comment.read', 'comment.create', 'comment.update',
        'report.create', 'user.read'
    );
    
    -- RESEARCHER permissions (includes all CLIENT permissions + more)
    INSERT INTO role_permissions (role_id, permission_id, is_granted)
    SELECT v_researcher_role_id, id, TRUE FROM permissions WHERE name IN (
        'plant.read', 'plant.create', 'plant.update', 'plant.verify',
        'compound.read', 'compound.create', 'compound.update', 'compound.verify',
        'article.read', 'article.create', 'article.update',
        'comment.read', 'comment.create', 'comment.update',
        'report.create', 'report.read',
        'user.read'
    );
    
    -- MODERATOR permissions
    INSERT INTO role_permissions (role_id, permission_id, is_granted)
    SELECT v_moderator_role_id, id, TRUE FROM permissions WHERE name IN (
        'plant.read', 'compound.read', 'article.read',
        'comment.read', 'comment.create', 'comment.update', 'comment.delete', 'comment.moderate',
        'report.read', 'user.read', 'user.update'
    );
    
    -- CODER_MAINTAINER permissions
    INSERT INTO role_permissions (role_id, permission_id, is_granted)
    SELECT v_coder_role_id, id, TRUE FROM permissions WHERE name LIKE 'system.%';
    
    -- ADMIN gets everything
    INSERT INTO role_permissions (role_id, permission_id, is_granted)
    SELECT v_admin_role_id, id, TRUE FROM permissions;
END $$;

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    
    -- Temporal validity
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Assignment context
    assigned_by UUID REFERENCES users(id),
    assignment_reason TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    UNIQUE(user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id) WHERE is_active = TRUE;
CREATE INDEX idx_user_roles_role ON user_roles(role_id) WHERE is_active = TRUE;
CREATE INDEX idx_user_roles_validity ON user_roles(valid_from, valid_until) WHERE is_active = TRUE;

COMMENT ON TABLE user_roles IS 'User role assignments with temporal validity';

-- User sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session data
    refresh_token VARCHAR(500) NOT NULL UNIQUE,
    
    -- Session metadata
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info JSONB,
    
    -- Validity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_refresh_token ON user_sessions(refresh_token) WHERE is_active = TRUE;
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);

COMMENT ON TABLE user_sessions IS 'User sessions with refresh tokens';
