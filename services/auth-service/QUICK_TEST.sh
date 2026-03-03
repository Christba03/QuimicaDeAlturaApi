#!/bin/bash

# Quick test script for auth service features
# Requires: curl, jq, and service running on localhost:8001

set -e

BASE_URL="http://localhost:8001/api/v1/auth"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Quick Auth Service Feature Tests${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if service is running
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo -e "${RED}Error: Auth service is not running on localhost:8001${NC}"
    echo "Start it with: docker-compose up -d auth-service"
    exit 1
fi

echo -e "${GREEN}✓ Service is running${NC}"
echo ""

# Test 1: Password Strength Validation
echo "1. Testing Password Strength Validation..."
echo "-------------------------------------------"

# Weak password (should fail)
WEAK_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/register" \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "weak@test.com",
    "password": "short",
    "first_name": "Test",
    "last_name": "User"
  }')

HTTP_CODE=$(echo "$WEAK_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "400" ]; then
    echo -e "${GREEN}  ✓ Weak password correctly rejected${NC}"
else
    echo -e "${RED}  ✗ Weak password not rejected (got $HTTP_CODE)${NC}"
fi

# Strong password (should succeed)
STRONG_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/register" \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "strong@test.com",
    "password": "StrongPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }')

HTTP_CODE=$(echo "$STRONG_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" == "201" ]; then
    echo -e "${GREEN}  ✓ Strong password accepted${NC}"
else
    echo -e "${RED}  ✗ Strong password rejected (got $HTTP_CODE)${NC}"
fi

echo ""

# Test 2: Rate Limiting
echo "2. Testing Rate Limiting..."
echo "----------------------------"

RATE_LIMITED=false
for i in {1..7}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/login" \
      -H 'Content-Type: application/json' \
      -d '{
        "email": "nonexistent@test.com",
        "password": "WrongPassword123!"
      }')
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" == "429" ]; then
        RATE_LIMITED=true
        RATE_LIMIT_HEADERS=$(curl -s -I -X POST "$BASE_URL/login" \
          -H 'Content-Type: application/json' \
          -d '{"email":"test@test.com","password":"test"}' | grep -i "rate")
        echo -e "${GREEN}  ✓ Rate limit triggered after $i attempts${NC}"
        if [ ! -z "$RATE_LIMIT_HEADERS" ]; then
            echo -e "${GREEN}  ✓ Rate limit headers present${NC}"
        fi
        break
    fi
    sleep 0.5
done

if [ "$RATE_LIMITED" == false ]; then
    echo -e "${YELLOW}  ⚠ Rate limit not triggered (may need more attempts)${NC}"
fi

echo ""

# Test 3: Device Fingerprinting
echo "3. Testing Device Fingerprinting..."
echo "-------------------------------------"

# Register and login
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/register" \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "device@test.com",
    "password": "StrongPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }')

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login" \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -d '{
    "email": "device@test.com",
    "password": "StrongPassword123!"
  }')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ ! -z "$TOKEN" ]; then
    # Get sessions
    SESSIONS_RESPONSE=$(curl -s -X GET "$BASE_URL/sessions/" \
      -H "Authorization: Bearer $TOKEN")
    
    DEVICE_NAME=$(echo "$SESSIONS_RESPONSE" | jq -r '.[0].device_name // empty')
    DEVICE_TYPE=$(echo "$SESSIONS_RESPONSE" | jq -r '.[0].device_type // empty')
    
    if [ ! -z "$DEVICE_NAME" ] && [ "$DEVICE_NAME" != "null" ]; then
        echo -e "${GREEN}  ✓ Device name captured: $DEVICE_NAME${NC}"
    else
        echo -e "${RED}  ✗ Device name not captured${NC}"
    fi
    
    if [ ! -z "$DEVICE_TYPE" ] && [ "$DEVICE_TYPE" != "null" ]; then
        echo -e "${GREEN}  ✓ Device type captured: $DEVICE_TYPE${NC}"
    else
        echo -e "${RED}  ✗ Device type not captured${NC}"
    fi
else
    echo -e "${RED}  ✗ Login failed, cannot test device fingerprinting${NC}"
fi

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "For comprehensive testing, see TESTING_GUIDE.md"
echo ""
