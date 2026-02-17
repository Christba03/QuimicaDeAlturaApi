# Database Strategy

## Overview

The platform uses a **hybrid database strategy** with domain-separated PostgreSQL instances, Redis for caching/sessions, and Elasticsearch for full-text search.

## Why Separate Databases?

1. **Independent scaling** - Each domain can scale independently based on load
2. **Fault isolation** - A problem in the chatbot DB doesn't affect plant data
3. **Security boundaries** - Auth data is physically separated from application data
4. **Optimized configuration** - Each DB can be tuned for its specific workload

## Database Instances

### postgres-core (Port 5432)
**Owner:** Plant Service
**Contains:** Core domain data
- `taxonomic_families` / `taxonomic_genera` - Taxonomy hierarchy
- `plants` / `plant_versions` / `plant_names` - Plant records with versioning
- `plant_verification_workflow` - Verification audit trail
- `chemical_compounds` / `plant_compounds` - Chemical data
- `medicinal_activities` / `plant_activities` - Medicinal uses
- `scientific_articles` + association tables - Literature references
- `genomic_sequences` / `blast_alignments` - Genomic data
- `data_sources` / `api_cache` - External data management
- `probability_weight_schemas` - Analytics weights

### postgres-auth (Port 5434)
**Owner:** Auth Service
**Contains:** Authentication & authorization
- `users` - User accounts with profile data
- `roles` / `permissions` / `role_permissions` - RBAC system
- `user_roles` - User-role assignments with temporal validity
- `user_sessions` - Session tracking (coordinated with Redis)

### postgres-chatbot (Port 5436)
**Owner:** Chatbot Service
**Contains:** Conversation data
- `conversations` / `messages` - Chat history
- `chatbot_knowledge_documents` - RAG knowledge base
- `chatbot_quick_replies` - Predefined responses
- `conversation_context` - Multi-turn context
- `chatbot_feedback` - User feedback on responses
- `intent_classification_log` - NLU analytics
- `conversation_flow_patterns` - Flow analytics

### postgres-user (Port 5435)
**Owner:** User Service
**Contains:** User interaction data
- `user_search_history` / `user_plant_views` - Browsing history
- `user_plant_favorites` - Saved plants
- `user_plant_usage_reports` - User experience reports
- `user_comments` / `comment_votes` - Community content
- `user_effectiveness_reports` / `user_side_effect_reports` - Health reports
- `sponsors` / `sponsored_plants` / `sponsored_compounds` - Sponsorship
- `recommendation_logs` - ML recommendation tracking
- `audit_log` / `data_quality_metrics` - System auditing

## Redis (Port 6379)

Redis is partitioned by database number:

| DB | Service | Use Case |
|----|---------|----------|
| 0 | Auth | Sessions, token blacklist, rate limiting |
| 1 | Plants | Plant data cache, search cache, view counters |
| 2 | Chatbot | Conversation context, RAG cache, presence |
| 3 | User | Profile cache, favorites cache, recent views |
| 4 | Search | Search results cache, autocomplete, popular terms |

See `database/redis/redis_schema.md` for complete key structure documentation.

## Elasticsearch (Port 9200)

Used by the Search Service for:
- Full-text search across plants, compounds, and activities
- Autocomplete/suggest functionality
- Faceted search and filtering
- Relevance-ranked results

## Cross-Service Data Access

Services that need data from another domain use **HTTP API calls** (not direct DB access):
- Chatbot Service -> Plant Service API for plant data
- User Service -> Auth Service API for user verification
- Search Service indexes data from Plant Service events

## Migration Strategy

Each service manages its own migrations using **Alembic**:
```bash
cd services/auth-service && alembic upgrade head
cd services/plant-service && alembic upgrade head
cd services/chatbot-service && alembic upgrade head
cd services/user-service && alembic upgrade head
```
