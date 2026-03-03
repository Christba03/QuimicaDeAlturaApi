#!/bin/bash

# Test script for new enterprise auth features
# This script tests all the new features without requiring Docker

set -e

echo "=========================================="
echo "Testing Enterprise Auth Features"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Must run from auth-service directory${NC}"
    exit 1
fi

echo "1. Testing Password Strength Validation..."
echo "-------------------------------------------"
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, 'src')

from utils.password_validator import validate_password, PasswordValidationError

# Test weak passwords
test_cases = [
    ("short", "at least 12 characters"),
    ("nouppercase123!", "uppercase"),
    ("NOLOWERCASE123!", "lowercase"),
    ("NoNumbers!", "number"),
    ("NoSpecial123", "special"),
]

passed = 0
failed = 0

for password, expected_error in test_cases:
    try:
        validate_password(password)
        print(f"  ✗ FAILED: '{password}' should have been rejected")
        failed += 1
    except PasswordValidationError as e:
        if expected_error.lower() in str(e).lower():
            print(f"  ✓ PASSED: '{password}' correctly rejected ({expected_error})")
            passed += 1
        else:
            print(f"  ✗ FAILED: '{password}' rejected but wrong reason: {e}")
            failed += 1

# Test strong password
try:
    validate_password("StrongPassword123!")
    print(f"  ✓ PASSED: Strong password accepted")
    passed += 1
except PasswordValidationError as e:
    print(f"  ✗ FAILED: Strong password rejected: {e}")
    failed += 1

print(f"\n  Results: {passed} passed, {failed} failed")
PYTHON_SCRIPT

echo ""
echo "2. Testing Device Fingerprinting..."
echo "-----------------------------------"
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, 'src')

from utils.device_fingerprint import (
    generate_device_fingerprint,
    detect_device_type,
    extract_device_name
)

# Test fingerprint generation
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
ip_address = "192.168.1.1"
accept_language = "en-US,en;q=0.9"

fingerprint1 = generate_device_fingerprint(user_agent, ip_address, accept_language)
fingerprint2 = generate_device_fingerprint(user_agent, ip_address, accept_language)

if fingerprint1 == fingerprint2 and len(fingerprint1) == 64:
    print(f"  ✓ PASSED: Device fingerprint generation (length: {len(fingerprint1)})")
else:
    print(f"  ✗ FAILED: Device fingerprint generation")
    print(f"    Fingerprint 1: {fingerprint1[:16]}...")
    print(f"    Fingerprint 2: {fingerprint2[:16]}...")

# Test device type detection
desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
tablet_ua = "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"

desktop_type = detect_device_type(desktop_ua)
mobile_type = detect_device_type(mobile_ua)
tablet_type = detect_device_type(tablet_ua)

if desktop_type == "desktop":
    print(f"  ✓ PASSED: Desktop detection")
else:
    print(f"  ✗ FAILED: Desktop detection (got: {desktop_type})")

if mobile_type == "mobile":
    print(f"  ✓ PASSED: Mobile detection")
else:
    print(f"  ✗ FAILED: Mobile detection (got: {mobile_type})")

if tablet_type == "tablet":
    print(f"  ✓ PASSED: Tablet detection")
else:
    print(f"  ✗ FAILED: Tablet detection (got: {tablet_type})")

# Test device name extraction
device_name = extract_device_name(desktop_ua)
if device_name and len(device_name) > 0:
    print(f"  ✓ PASSED: Device name extraction ('{device_name}')")
else:
    print(f"  ✗ FAILED: Device name extraction")
PYTHON_SCRIPT

echo ""
echo "3. Testing Configuration..."
echo "---------------------------"
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, 'src')

from config import settings

# Check all new configuration options
configs_to_check = [
    ("PASSWORD_MIN_LENGTH", settings.PASSWORD_MIN_LENGTH, 12),
    ("PASSWORD_MIN_STRENGTH_SCORE", settings.PASSWORD_MIN_STRENGTH_SCORE, 3),
    ("PASSWORD_HISTORY_SIZE", settings.PASSWORD_HISTORY_SIZE, 5),
    ("RATE_LIMIT_ENABLED", settings.RATE_LIMIT_ENABLED, True),
    ("RATE_LIMIT_LOGIN_PER_15MIN", settings.RATE_LIMIT_LOGIN_PER_15MIN, 5),
    ("TRUSTED_DEVICE_DURATION_DAYS", settings.TRUSTED_DEVICE_DURATION_DAYS, 30),
    ("EMAIL_QUEUE_ENABLED", settings.EMAIL_QUEUE_ENABLED, True),
]

passed = 0
failed = 0

for config_name, actual_value, expected_value in configs_to_check:
    if actual_value == expected_value:
        print(f"  ✓ {config_name} = {actual_value}")
        passed += 1
    else:
        print(f"  ✗ {config_name} = {actual_value} (expected {expected_value})")
        failed += 1

print(f"\n  Results: {passed} passed, {failed} failed")
PYTHON_SCRIPT

echo ""
echo "4. Checking Imports..."
echo "----------------------"
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, 'src')

modules_to_check = [
    ("password_validator", "utils.password_validator"),
    ("device_fingerprint", "utils.device_fingerprint"),
    ("rate_limit_service", "services.rate_limit_service"),
    ("rate_limit middleware", "middleware.rate_limit"),
    ("email_queue", "services.email_queue"),
    ("email_worker", "workers.email_worker"),
]

passed = 0
failed = 0

for module_name, module_path in modules_to_check:
    try:
        __import__(module_path)
        print(f"  ✓ {module_name} imported successfully")
        passed += 1
    except ImportError as e:
        print(f"  ✗ {module_name} import failed: {e}")
        failed += 1

print(f"\n  Results: {passed} passed, {failed} failed")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo -e "${YELLOW}Note:${NC} For full integration tests, start the services:"
echo "  docker-compose up -d"
echo ""
echo "Then test the API endpoints with:"
echo "  python3 -m pytest tests/test_new_features.py -v"
echo ""
echo "Or use curl/httpie to test manually:"
echo ""
echo "  # Test password strength (should fail)"
echo "  curl -X POST http://localhost:8001/api/v1/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"password\":\"weak\",\"first_name\":\"Test\",\"last_name\":\"User\"}'"
echo ""
echo "  # Test password strength (should succeed)"
echo "  curl -X POST http://localhost:8001/api/v1/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"password\":\"StrongPassword123!\",\"first_name\":\"Test\",\"last_name\":\"User\"}'"
echo ""
