# Quick Start Guide

## Infrastructure Status ✅

All infrastructure services are running and healthy:
- ✅ Redis (mp-redis)
- ✅ Elasticsearch (mp-elasticsearch)
- ✅ PostgreSQL Core (mp-postgres-core)
- ✅ PostgreSQL Auth (mp-postgres-auth)
- ✅ PostgreSQL Chatbot (mp-postgres-chatbot)
- ✅ PostgreSQL User (mp-postgres-user)

## Next Steps

### 1. Start Application Services

```bash
# Start all services
make up

# Or start specific services
make auth      # Auth service only
make gateway   # API Gateway
make plant     # Plant service
```

### 2. Run Database Migrations

```bash
# Run all migrations
make migrate

# Or run auth service migrations specifically
make migrate-auth
```

### 3. Verify Services

```bash
# Check service health
curl http://localhost:8001/health  # Auth service
curl http://localhost:8000/health   # API Gateway

# View logs
make logs SERVICE=auth-service
```

### 4. Run Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-ci
```

### 5. Access Services

- **API Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Plant Service**: http://localhost:8002
- **Chatbot Service**: http://localhost:8003
- **Search Service**: http://localhost:8004
- **User Service**: http://localhost:8005

## Common Commands

```bash
# View all available commands
make help

# Start everything
make up

# Stop everything
make down

# View logs
make logs

# Rebuild services
make rebuild

# Clean up
make clean
```

## Troubleshooting

### Port Conflicts

If you encounter port conflicts:
```bash
# Stop conflicting services
make stop-redis

# Or use different ports
REDIS_PORT=6380 make up
```

### Service Not Starting

```bash
# Check logs
make logs SERVICE=auth-service

# Check service status
docker compose ps

# Restart service
make restart SERVICE=auth-service
```

### Database Issues

```bash
# Check database connection
docker compose exec postgres-auth psql -U mp_auth_user -d medicinal_plants_auth

# Run migrations
make migrate-auth
```

## Development Workflow

1. **Start infrastructure** (already done ✅)
   ```bash
   make infra
   ```

2. **Start services**
   ```bash
   make up
   ```

3. **Run migrations**
   ```bash
   make migrate
   ```

4. **Develop & Test**
   ```bash
   make test
   make lint
   ```

5. **Deploy**
   ```bash
   make deploy
   ```

## CI/CD

### Run CI Pipeline Locally

```bash
make ci
```

### Start Jenkins

```bash
make jenkins-up
# Access at http://localhost:8080
```

### GitHub Actions

Push to GitHub and workflows will run automatically!
