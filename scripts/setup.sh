#!/usr/bin/env bash
set -euo pipefail

echo "=== Medicinal Plants Platform - Setup ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Error: docker is required"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Error: docker compose is required"; exit 1; }

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration values."
else
    echo ".env already exists, skipping."
fi

# Build all services
echo "Building all services..."
docker compose build

# Start infrastructure
echo "Starting infrastructure (databases, Redis, Elasticsearch)..."
docker compose up -d postgres-core postgres-auth postgres-chatbot postgres-user redis elasticsearch

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
for service in postgres-core postgres-auth postgres-chatbot postgres-user; do
    echo "  Waiting for $service..."
    until docker compose exec -T $service pg_isready -q 2>/dev/null; do
        sleep 1
    done
    echo "  $service is ready."
done

echo "Waiting for Redis..."
until docker compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-dev_redis_password}" ping 2>/dev/null | grep -q PONG; do
    sleep 1
done
echo "  Redis is ready."

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Run database migrations:  make migrate"
echo "  2. Seed sample data:         make seed"
echo "  3. Start all services:       make up"
echo "  4. Check health:             curl http://localhost:8000/health"
echo ""
