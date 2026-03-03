# Testing Guide for Enterprise Auth Features

This guide explains how to test all the new enterprise-level authentication features.

## Prerequisites

1. **Start Infrastructure Services:**
   ```bash
   docker-compose up -d postgres-auth redis
   ```

2. **Install Dependencies:**
   ```bash
   cd services/auth-service
   pip install -r requirements.txt
   ```

3. **Run Database Migrations:**
   ```bash
   # From auth-service directory
   alembic upgrade head
   ```

4. **Start Auth Service:**
   ```bash
   # Option 1: Using Docker
   docker-compose up -d auth-service
   
   # Option 2: Direct Python
   uvicorn src.main:app --host 0.0.0.0 --port 8001
   ```

5. **Start Email Worker (Optional, for async email queue):**
   ```bash
   # From auth-service directory
   arq src.workers.email_worker.WorkerSettings
   ```

## Feature Tests

### 1. Password Strength Validation

**Test Weak Passwords (Should Fail):**

```bash
# Too short
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test1@example.com",
    "password": "Short1!",
    "first_name": "Test",
    "last_name": "User"
  }'

# No uppercase
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test2@example.com",
    "password": "lowercase123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# No lowercase
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test3@example.com",
    "password": "UPPERCASE123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# No number
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test4@example.com",
    "password": "NoNumbers!",
    "first_name": "Test",
    "last_name": "User"
  }'

# No special character
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test5@example.com",
    "password": "NoSpecial123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Test Strong Password (Should Succeed):**

```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "StrongPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Expected Response:** `201 Created` with user data

### 2. Password History

**Test Password Reuse Prevention:**

```bash
# 1. Register user
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "history@example.com",
    "password": "InitialPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# 2. Login to get token
TOKEN=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "history@example.com",
    "password": "InitialPassword123!"
  }' | jq -r '.access_token')

# 3. Change password
curl -X POST http://localhost:8001/api/v1/users/me/password \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "current_password": "InitialPassword123!",
    "new_password": "NewPassword123!"
  }'

# 4. Try to change back to old password (should fail)
curl -X POST http://localhost:8001/api/v1/users/me/password \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "current_password": "NewPassword123!",
    "new_password": "InitialPassword123!"
  }'
```

**Expected Response:** `400 Bad Request` with message about password reuse

### 3. Rate Limiting

**Test Login Rate Limit:**

```bash
# Try to login multiple times rapidly
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{
      "email": "test@example.com",
      "password": "WrongPassword123!"
    }' \
    -v 2>&1 | grep -E "(HTTP|X-RateLimit|429)"
  sleep 0.5
done
```

**Expected:** After 5 attempts (default limit), you should get `429 Too Many Requests` with rate limit headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`
- `Retry-After`

**Test Registration Rate Limit:**

```bash
# Try to register multiple times rapidly
for i in {1..5}; do
  curl -X POST http://localhost:8001/api/v1/auth/register \
    -H 'Content-Type: application/json' \
    -d "{
      \"email\": \"test$i@example.com\",
      \"password\": \"StrongPassword123!\",
      \"first_name\": \"Test\",
      \"last_name\": \"User\"
    }"
done
```

**Expected:** After 3 attempts (default limit), you should get `429 Too Many Requests`

### 4. Device Fingerprinting

**Test Device Tracking:**

```bash
# 1. Register and login
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "device@example.com",
    "password": "StrongPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'

TOKEN=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -d '{
    "email": "device@example.com",
    "password": "StrongPassword123!"
  }' | jq -r '.access_token')

# 2. Get sessions (should show device info)
curl -X GET http://localhost:8001/api/v1/auth/sessions/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected response includes:
# - device_name: "Chrome on Windows"
# - device_type: "desktop"
# - device_fingerprint: (hash)
# - is_trusted: false
```

**Test Trusted Device:**

```bash
# 1. Get session ID from sessions list
SESSION_ID=$(curl -X GET http://localhost:8001/api/v1/auth/sessions/ \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

# 2. Mark device as trusted
curl -X POST http://localhost:8001/api/v1/auth/devices/trust/$SESSION_ID \
  -H "Authorization: Bearer $TOKEN"

# 3. Login again from same device (should skip 2FA if enabled)
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -d '{
    "email": "device@example.com",
    "password": "StrongPassword123!"
  }' | jq '.'
```

**Test Device List:**

```bash
curl -X GET http://localhost:8001/api/v1/auth/devices \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

### 5. Async Email Queue

**Test Email Queue Status:**

```bash
# Check if email queue is enabled in config
curl http://localhost:8001/health | jq '.'

# The email queue should be processing emails asynchronously
# Check logs for email worker:
docker-compose logs auth-service | grep email
```

**Test Email Verification:**

```bash
# Register user (should trigger verification email)
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "verify@example.com",
    "password": "StrongPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# Check email worker logs for queued email
# If EMAIL_QUEUE_ENABLED=true, email should be queued
# If EMAIL_QUEUE_ENABLED=false, email should be sent synchronously
```

## Integration Test Script

Run the comprehensive test script:

```bash
cd services/auth-service
python3 -m pytest tests/test_new_features.py -v
```

## Manual Testing Checklist

- [ ] Password strength validation rejects weak passwords
- [ ] Password strength validation accepts strong passwords
- [ ] Password history prevents reuse of recent passwords
- [ ] Rate limiting works on login endpoint
- [ ] Rate limiting works on registration endpoint
- [ ] Rate limit headers are present in responses
- [ ] Device fingerprinting tracks device information
- [ ] Device type detection works (mobile/desktop/tablet)
- [ ] Device name extraction works
- [ ] Trusted device marking works
- [ ] Trusted devices skip 2FA
- [ ] Device list endpoint returns device info
- [ ] Email queue processes emails asynchronously (if enabled)
- [ ] Email fallback works if queue is disabled

## Troubleshooting

### Rate Limiting Not Working
- Check Redis connection: `docker-compose ps redis`
- Check Redis logs: `docker-compose logs redis`
- Verify `RATE_LIMIT_ENABLED=true` in config

### Device Fingerprinting Not Working
- Check that User-Agent header is being sent
- Verify database migration ran: `alembic current`
- Check session table has device columns

### Email Queue Not Working
- Check if email worker is running: `ps aux | grep arq`
- Check Redis connection for ARQ
- Verify `EMAIL_QUEUE_ENABLED=true` in config
- Check SMTP settings are correct

### Password History Not Working
- Verify migration `002_add_password_history.py` ran
- Check `users` table has `password_history` column
- Verify `PASSWORD_HISTORY_SIZE` is set correctly

## Performance Testing

Test rate limiting under load:

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test login endpoint rate limit
ab -n 100 -c 10 -p login.json -T application/json \
  http://localhost:8001/api/v1/auth/login
```

## Security Testing

1. **Brute Force Protection:** Try multiple failed logins
2. **Password Spraying:** Test with common passwords
3. **Session Hijacking:** Test device fingerprint changes
4. **Rate Limit Bypass:** Test with different IPs (if behind proxy)
