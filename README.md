# Sistema Inteligente de Análisis de Plantas Medicinales de México

Microservices-based platform for the analysis and management of Mexican medicinal plants data.

## Architecture

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | Request routing, rate limiting, auth middleware |
| Auth Service | 8001 | Authentication, authorization, session management |
| Plant Service | 8002 | Plant data, compounds, activities, verification |
| Chatbot Service | 8003 | AI-powered chatbot with RAG |
| Search Service | 8004 | Full-text search, autocomplete, recommendations |
| User Service | 8005 | User profiles, favorites, usage reports |

## Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your values

# 2. Start infrastructure
make infra

# 3. Build and start all services
make up

# 4. Verify health
curl http://localhost:8000/health
```

## Database Strategy

Hybrid approach with domain-separated databases:

| Database | Port | Domain |
|----------|------|--------|
| postgres-core | 5432 | Plants, compounds, activities, articles |
| postgres-auth | 5434 | Users, roles, permissions, sessions |
| postgres-chatbot | 5436 | Conversations, messages, knowledge base |
| postgres-user | 5435 | Favorites, usage reports, history |

Redis is used for caching, sessions, and rate limiting across all services.

## Development

```bash
make help          # Show all available commands
make infra         # Start databases and Redis only
make build         # Build all service images
make up            # Start everything
make logs          # View logs (SERVICE=auth-service for specific)
make test          # Run all tests
make monitoring    # Start Prometheus + Grafana + Loki
```

## Tech Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **Databases**: PostgreSQL 16, Redis 7, Elasticsearch 8
- **AI/ML**: Anthropic Claude API, RAG pipeline
- **Monitoring**: Prometheus, Grafana, Loki, Alertmanager
- **Container**: Docker + Docker Compose
