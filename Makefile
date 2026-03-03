.PHONY: help up down build logs restart clean migrate seed test lint infra monitoring deploy jenkins-up jenkins-down

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================
# Docker Compose
# ==========================================

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build all Docker images
	docker compose build

build-optimized: ## Build with optimizations (BuildKit, cache)
	@DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker compose build

build-prod: ## Build production images with optimizations
	@./scripts/build-optimized.sh all

build-auth: ## Build auth service only
	docker compose build auth-service

build-auth-prod: ## Build auth service with production optimizations
	@DOCKER_BUILDKIT=1 docker build -f services/auth-service/Dockerfile.prod \
		-t quimicadealtura_api-auth-service:prod \
		--cache-from quimicadealtura_api-auth-service:latest \
		services/auth-service

rebuild: ## Rebuild and restart all services
	docker compose up -d --build

logs: ## Show logs for all services (use SERVICE=name to filter)
	docker compose logs -f $(SERVICE)

restart: ## Restart a specific service (use SERVICE=name)
	docker compose restart $(SERVICE)

clean: ## Stop and remove all containers, volumes, and networks
	docker compose down -v --remove-orphans
	docker compose -f docker-compose.monitoring.yml down -v --remove-orphans

stop-redis: ## Stop Redis processes/containers using port 6379
	@./scripts/stop-redis.sh

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

migrate-auth: ## Run database migrations for auth service only
	docker-compose exec auth-service alembic upgrade head || docker-compose run --rm auth-service alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create NAME=migration_name SERVICE=auth-service)
	cd services/$(SERVICE) && alembic revision --autogenerate -m "$(NAME)"

seed: ## Seed databases with sample data
	./scripts/seed-data.sh

# ==========================================
# Development
# ==========================================

setup: ## Initial project setup
	./scripts/setup.sh

test: ## Run all tests (pre-deployment test suite)
	@echo "Running test suite..."
	@./scripts/pre-deploy-test.sh

test-unit: ## Run unit tests only (use SERVICE=name to filter)
ifdef SERVICE
	cd services/$(SERVICE) && python -m pytest tests/ -v
else
	@for dir in services/*/; do \
		echo "Testing $$dir..."; \
		cd $$dir && python -m pytest tests/ -v 2>/dev/null || true; \
		cd ../..; \
	done
endif

test-integration: ## Run integration tests
	@echo "Starting services..."
	docker compose up -d postgres-auth redis auth-service
	@sleep 10
	@cd services/auth-service && ./QUICK_TEST.sh

test-ci: ## Run CI test suite
	@./scripts/ci-test.sh

lint: ## Lint all services
	@for dir in services/*/; do \
		echo "Linting $$dir..."; \
		cd $$dir && python -m ruff check src/ 2>/dev/null || python -m flake8 src --max-line-length=120 --exclude=__pycache__,*.pyc 2>/dev/null || true; \
		cd ../..; \
	done

lint-fix: ## Fix linting issues (use SERVICE=name to filter)
ifdef SERVICE
	cd services/$(SERVICE) && black src && isort src
else
	@for dir in services/*/; do \
		echo "Fixing linting in $$dir..."; \
		cd $$dir && (black src && isort src) 2>/dev/null || true; \
		cd ../..; \
	done
endif

setup-ci: ## Setup CI environment
	@echo "Setting up CI environment..."
	@pip install -q flake8 black isort pytest httpx requests
	@echo "✓ CI environment ready"

ci: setup-ci lint test-ci ## Run full CI pipeline

# ==========================================
# Build Cache Management
# ==========================================

cache-save: ## Save build cache
	@./scripts/build-cache.sh save

cache-stats: ## Show build cache statistics
	@./scripts/build-cache.sh stats

cache-clear: ## Clear build cache
	@./scripts/build-cache.sh clear

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

# ==========================================
# CI/CD & Deployment
# ==========================================

deploy: test ## Deploy after tests pass
	@echo "✅ All tests passed! Ready for deployment."
	@echo "Deployment steps:"
	@echo "  1. Tag Docker images"
	@echo "  2. Push to registry"
	@echo "  3. Update production environment"

jenkins-up: ## Start Jenkins server
	cd jenkins && docker-compose up -d
	@echo "Jenkins is starting at http://localhost:8080"
	@echo "Initial admin password:"
	@docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "Jenkins container not running yet"

jenkins-down: ## Stop Jenkins server
	cd jenkins && docker-compose down

jenkins-logs: ## View Jenkins logs
	docker logs -f jenkins
