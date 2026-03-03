#!/bin/bash

# Pre-deployment test script
# This script runs all tests before deployment to ensure everything works

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Pre-Deployment Test Suite${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED: $test_name${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
    echo ""
}

# Test 1: Build Docker images
run_test "Build Docker Images" "
    docker-compose build auth-service
"

# Test 2: Start infrastructure
run_test "Start Infrastructure" "
    docker-compose up -d postgres-auth redis && \
    sleep 10 && \
    docker-compose ps | grep -q 'postgres-auth.*healthy' && \
    docker-compose ps | grep -q 'redis.*healthy'
"

# Test 3: Database migrations
run_test "Database Migrations" "
    docker-compose exec -T auth-service alembic upgrade head || \
    docker-compose run --rm auth-service alembic upgrade head
"

# Test 4: Service health check
run_test "Service Health Check" "
    docker-compose up -d auth-service && \
    sleep 10 && \
    curl -f http://localhost:8001/health > /dev/null
"

# Test 5: Password validation
run_test "Password Validation" "
    docker-compose exec -T auth-service python3 -c \"
import sys
sys.path.insert(0, 'src')
from utils.password_validator import validate_password, PasswordValidationError

# Test weak password
try:
    validate_password('short')
    sys.exit(1)
except PasswordValidationError:
    pass

# Test strong password
validate_password('StrongPassword123!')
print('Password validation OK')
\"
"

# Test 6: Device fingerprinting
run_test "Device Fingerprinting" "
    docker-compose exec -T auth-service python3 -c \"
import sys
sys.path.insert(0, 'src')
from utils.device_fingerprint import generate_device_fingerprint, detect_device_type

fp = generate_device_fingerprint('Mozilla/5.0', '192.168.1.1', 'en-US')
assert len(fp) == 64
assert detect_device_type('Mozilla/5.0 (iPhone') == 'mobile'
print('Device fingerprinting OK')
\"
"

# Test 7: API endpoints
run_test "API Endpoints" "
    curl -f http://localhost:8001/health > /dev/null && \
    curl -f http://localhost:8001/docs > /dev/null
"

# Test 8: Rate limiting (basic check)
run_test "Rate Limiting Check" "
    RESPONSE_CODE=\$(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8001/api/v1/auth/login \\
        -H 'Content-Type: application/json' \\
        -d '{\"email\":\"test@test.com\",\"password\":\"wrong\"}')
    [ \"\$RESPONSE_CODE\" == \"401\" ] || [ \"\$RESPONSE_CODE\" == \"429\" ]
"

# Test 9: Password strength API
run_test "Password Strength API" "
    RESPONSE_CODE=\$(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8001/api/v1/auth/register \\
        -H 'Content-Type: application/json' \\
        -d '{\"email\":\"weak@test.com\",\"password\":\"short\",\"first_name\":\"Test\",\"last_name\":\"User\"}')
    [ \"\$RESPONSE_CODE\" == \"400\" ]
"

# Test 10: Configuration check
run_test "Configuration Check" "
    docker-compose exec -T auth-service python3 -c \"
import sys
sys.path.insert(0, 'src')
from config import settings

assert hasattr(settings, 'PASSWORD_MIN_LENGTH')
assert hasattr(settings, 'RATE_LIMIT_ENABLED')
assert hasattr(settings, 'EMAIL_QUEUE_ENABLED')
print('Configuration OK')
\"
"

# Summary
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please fix issues before deploying.${NC}"
    exit 1
fi
