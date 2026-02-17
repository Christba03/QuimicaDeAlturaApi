.PHONY: help up down build logs restart clean migrate seed test lint infra monitoring

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================
# Docker Compose
# ==========================================

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build all services
	docker compose build

rebuild: ## Rebuild and restart all services
	docker compose up -d --build

logs: ## Show logs for all services (use SERVICE=name to filter)
	docker compose logs -f $(SERVICE)

restart: ## Restart a specific service (use SERVICE=name)
	docker compose restart $(SERVICE)

clean: ## Stop and remove all containers, volumes, and networks
	docker compose down -v --remove-orphans
	docker compose -f docker-compose.monitoring.yml down -v --remove-orphans

# ==========================================
# Infrastructure Only
# ==========================================

infra: ## Start only infrastructure (databases, Redis, Elasticsearch)
	docker compose up -d postgres-core postgres-auth postgres-chatbot postgres-user redis elasticsearch

infra-down: ## Stop infrastructure
	docker compose stop postgres-core postgres-auth postgres-chatbot postgres-user redis elasticsearch

# ==========================================
# Monitoring
# ==========================================

monitoring: ## Start monitoring stack
	docker compose -f docker-compose.monitoring.yml up -d

monitoring-down: ## Stop monitoring stack
	docker compose -f docker-compose.monitoring.yml down

# ==========================================
# Database
# ==========================================

migrate: ## Run database migrations for all services
	./scripts/migrate-db.sh

seed: ## Seed databases with sample data
	./scripts/seed-data.sh

# ==========================================
# Development
# ==========================================

setup: ## Initial project setup
	./scripts/setup.sh

test: ## Run tests for all services (use SERVICE=name to filter)
ifdef SERVICE
	cd services/$(SERVICE) && python -m pytest tests/ -v
else
	@for dir in services/*/; do \
		echo "Testing $$dir..."; \
		cd $$dir && python -m pytest tests/ -v 2>/dev/null || true; \
		cd ../..; \
	done
endif

lint: ## Lint all services
	@for dir in services/*/; do \
		echo "Linting $$dir..."; \
		cd $$dir && python -m ruff check src/ 2>/dev/null || true; \
		cd ../..; \
	done

# ==========================================
# Individual Services
# ==========================================

gateway: ## Start API Gateway only
	docker compose up -d api-gateway

auth: ## Start Auth Service only
	docker compose up -d auth-service

plant: ## Start Plant Service only
	docker compose up -d plant-service

chatbot: ## Start Chatbot Service only
	docker compose up -d chatbot-service

search: ## Start Search Service only
	docker compose up -d search-service

user: ## Start User Service only
	docker compose up -d user-service
