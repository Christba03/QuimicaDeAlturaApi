# Build and Test Guide

This guide explains how to build the microservices and test all the new enterprise auth features.

## Quick Start

### 1. Build All Services

```bash
# Build all services
docker-compose build

# Or build specific service
docker-compose build auth-service
```

### 2. Start Infrastructure

```bash
# Start databases and Redis
docker-compose up -d postgres-auth redis

# Wait for services to be healthy
docker-compose ps
```

### 3. Run Database Migrations

```bash
# Run migrations for auth service
docker-compose exec auth-service alembic upgrade head

# Or manually
cd services/auth-service
alembic upgrade head
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Or start specific service
docker-compose up -d auth-service

# View logs
docker-compose logs -f auth-service
```

### 5. Start Email Worker (Optional)

```bash
# Start ARQ worker for async email processing
docker-compose exec auth-service arq src.workers.email_worker.WorkerSettings

# Or run in separate container
docker-compose run --rm auth-service arq src.workers.email_worker.WorkerSettings
```

## Testing

### Quick Test Script

```bash
# Run quick test (requires service to be running)
cd services/auth-service
./QUICK_TEST.sh
```

### Comprehensive Tests

```bash
# Install test dependencies
cd services/auth-service
pip install -r requirements.txt pytest httpx

# Run pytest tests
pytest tests/test_new_features.py -v

# Run with coverage
pytest tests/test_new_features.py --cov=src --cov-report=html
```

### Manual API Testing

See `services/auth-service/TESTING_GUIDE.md` for detailed API testing instructions.

## Feature Verification Checklist

### ✅ Password Strength Validation
- [ ] Weak passwords (< 12 chars) rejected
- [ ] Passwords without uppercase rejected
- [ ] Passwords without lowercase rejected
- [ ] Passwords without numbers rejected
- [ ] Passwords without special chars rejected
- [ ] Strong passwords accepted
- [ ] zxcvbn score validation works

### ✅ Password History
- [ ] Password history stored in database
- [ ] Recent passwords cannot be reused
- [ ] History size limited to configured value
- [ ] History checked on password change
- [ ] History checked on password reset

### ✅ Rate Limiting
- [ ] Login endpoint rate limited
- [ ] Registration endpoint rate limited
- [ ] Password reset endpoint rate limited
- [ ] Rate limit headers present
- [ ] Rate limit works across instances (Redis)
- [ ] Rate limit resets after window

### ✅ Device Fingerprinting
- [ ] Device fingerprint generated correctly
- [ ] Device type detected (mobile/desktop/tablet)
- [ ] Device name extracted
- [ ] Fingerprint stored in session
- [ ] Same device produces same fingerprint
- [ ] Different devices produce different fingerprints

### ✅ Trusted Devices
- [ ] Devices can be marked as trusted
- [ ] Trusted status stored in database
- [ ] Trusted devices skip 2FA
- [ ] Trust status expires after configured duration
- [ ] Trust status can be revoked
- [ ] Device list shows trust status

### ✅ Async Email Queue
- [ ] Emails queued when queue enabled
- [ ] Emails sent synchronously when queue disabled
- [ ] Email worker processes queue
- [ ] Failed emails retried
- [ ] Email templates rendered correctly
- [ ] Fallback to sync on queue failure

## Troubleshooting

### Build Issues

```bash
# Clean build
docker-compose build --no-cache auth-service

# Check Dockerfile syntax
docker build -t test-auth ./services/auth-service
```

### Database Issues

```bash
# Check database connection
docker-compose exec postgres-auth psql -U mp_auth_user -d medicinal_plants_auth

# Check migrations
docker-compose exec auth-service alembic current
docker-compose exec auth-service alembic history

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d postgres-auth
docker-compose exec auth-service alembic upgrade head
```

### Redis Issues

```bash
# Check Redis connection
docker-compose exec redis redis-cli -a dev_redis_password ping

# Check rate limit keys
docker-compose exec redis redis-cli -a dev_redis_password KEYS "rate_limit:*"

# Check email queue
docker-compose exec redis redis-cli -a dev_redis_password KEYS "arq:*"
```

### Service Issues

```bash
# Check service health
curl http://localhost:8001/health

# Check service logs
docker-compose logs -f auth-service

# Check service status
docker-compose ps auth-service
```

## Environment Variables

Key environment variables for auth service:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=dev_redis_password
REDIS_DB=0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password
SMTP_FROM=noreply@example.com

# Password Policy
PASSWORD_MIN_LENGTH=12
PASSWORD_MIN_STRENGTH_SCORE=3
PASSWORD_HISTORY_SIZE=5

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN_PER_15MIN=5
RATE_LIMIT_REGISTER_PER_HOUR=3

# Device Trust
TRUSTED_DEVICE_DURATION_DAYS=30
REQUIRE_2FA_FOR_NEW_DEVICES=true

# Email Queue
EMAIL_QUEUE_ENABLED=true
EMAIL_QUEUE_MAX_RETRIES=3
EMAIL_QUEUE_RETRY_DELAY_SECONDS=60
```

## Next Steps

1. **Configure SMTP** for email functionality
2. **Set up monitoring** for rate limits and email queue
3. **Configure production secrets** (JWT keys, passwords)
4. **Set up CI/CD** for automated testing
5. **Load testing** for rate limiting
6. **Security audit** of all endpoints

## Additional Resources

- [Testing Guide](./services/auth-service/TESTING_GUIDE.md)
- [API Documentation](http://localhost:8001/docs) (when service is running)
- [Alembic Migrations](./services/auth-service/alembic/versions/)
