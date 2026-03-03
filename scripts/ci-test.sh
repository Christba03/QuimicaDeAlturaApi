#!/bin/bash

# CI/CD test script for Jenkins/GitHub Actions
# Runs comprehensive tests in CI environment

set -e

echo "=========================================="
echo "CI/CD Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SERVICE_URL="${SERVICE_URL:-http://localhost:8001}"
MAX_WAIT_TIME=60

# Function to wait for service
wait_for_service() {
    local url=$1
    local max_attempts=$2
    local attempt=0
    
    echo "Waiting for service at $url..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -f "$url/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Service is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Attempt $attempt/$max_attempts..."
        sleep 2
    done
    
    echo -e "${RED}✗ Service did not become ready${NC}"
    return 1
}

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_code=$5
    
    echo -n "Testing $name... "
    
    if [ -z "$data" ]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" -X "$method" "$SERVICE_URL$endpoint")
    else
        RESPONSE=$(curl -s -w "\n%{http_code}" -X "$method" "$SERVICE_URL$endpoint" \
            -H 'Content-Type: application/json' \
            -d "$data")
    fi
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $HTTP_CODE)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_code, got $HTTP_CODE)"
        return 1
    fi
}

# Start services
echo "Starting services..."
docker-compose up -d postgres-auth redis
sleep 5

# Run migrations
echo "Running migrations..."
docker-compose exec -T auth-service alembic upgrade head || \
docker-compose run --rm auth-service alembic upgrade head

# Start auth service
echo "Starting auth service..."
docker-compose up -d auth-service

# Wait for service
wait_for_service "$SERVICE_URL" 30

# Run tests
echo ""
echo "Running API tests..."
echo "-------------------"

TESTS_PASSED=0
TESTS_FAILED=0

# Health check
test_endpoint "Health Check" "GET" "/health" "" "200" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))

# API docs
test_endpoint "API Documentation" "GET" "/docs" "" "200" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))

# Registration with weak password (should fail)
test_endpoint "Weak Password Rejection" "POST" "/api/v1/auth/register" \
    '{"email":"weak@test.com","password":"short","first_name":"Test","last_name":"User"}' \
    "400" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))

# Registration with strong password (should succeed)
test_endpoint "Strong Password Acceptance" "POST" "/api/v1/auth/register" \
    '{"email":"strong@test.com","password":"StrongPassword123!","first_name":"Test","last_name":"User"}' \
    "201" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))

# Login with wrong password (should fail)
test_endpoint "Invalid Login" "POST" "/api/v1/auth/login" \
    '{"email":"nonexistent@test.com","password":"wrong"}' \
    "401" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
