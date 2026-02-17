#!/usr/bin/env bash
set -euo pipefail

echo "=== Seeding Databases ==="

# Seed auth database (roles and permissions)
echo "Seeding auth database..."
for sql_file in database/postgres/seeds/01_roles_permissions.sql; do
    if [ -f "$sql_file" ]; then
        docker compose exec -T postgres-auth psql \
            -U "${POSTGRES_AUTH_USER:-mp_auth_user}" \
            -d "${POSTGRES_AUTH_DB:-medicinal_plants_auth}" \
            < "$sql_file" 2>&1 || echo "Warning: Seed $sql_file may have already been applied"
    fi
done

# Seed chatbot database (knowledge base)
echo "Seeding chatbot database..."
for sql_file in database/postgres/seeds/02_sample_knowledge_base.sql; do
    if [ -f "$sql_file" ]; then
        docker compose exec -T postgres-chatbot psql \
            -U "${POSTGRES_CHATBOT_USER:-mp_chatbot_user}" \
            -d "${POSTGRES_CHATBOT_DB:-medicinal_plants_chatbot}" \
            < "$sql_file" 2>&1 || echo "Warning: Seed $sql_file may have already been applied"
    fi
done

echo ""
echo "=== Seeding complete ==="
