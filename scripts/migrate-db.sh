#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Database Migrations ==="

SERVICES_WITH_DB=("auth-service" "plant-service" "chatbot-service" "user-service")

for service in "${SERVICES_WITH_DB[@]}"; do
    echo ""
    echo "--- Migrating $service ---"
    if [ -f "services/$service/alembic.ini" ]; then
        docker compose exec -T "$service" alembic upgrade head 2>&1 || {
            echo "Warning: Migration failed for $service (service may not be running)"
            echo "  Try: docker compose up -d $service && make migrate"
        }
    else
        echo "  No alembic.ini found, skipping."
    fi
done

echo ""
echo "=== Migrations complete ==="
