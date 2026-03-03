# CI/CD Setup Guide

This guide explains how to set up automated testing and deployment using Jenkins or GitHub Actions.

## Quick Start

### Option 1: Jenkins (Self-Hosted)

1. **Start Jenkins:**
   ```bash
   cd jenkins
   docker-compose up -d
   ```

2. **Get initial admin password:**
   ```bash
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```

3. **Access Jenkins:**
   - Open http://localhost:8080
   - Enter admin password
   - Install suggested plugins
   - Create admin user

4. **Create Pipeline Job:**
   - Click "New Item"
   - Enter job name
   - Select "Pipeline"
   - In Pipeline configuration:
     - Definition: Pipeline script from SCM
     - SCM: Git
     - Repository URL: Your repository URL
     - Script Path: Jenkinsfile

5. **Run Pipeline:**
   - Click "Build Now"
   - Monitor progress in Blue Ocean or classic view

### Option 2: GitHub Actions (Cloud)

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Add CI/CD pipeline"
   git push
   ```

2. **View Actions:**
   - Go to GitHub repository
   - Click "Actions" tab
   - See workflow runs automatically

## Pipeline Stages

The CI/CD pipeline includes:

1. **Checkout** - Get latest code
2. **Lint & Code Quality** - Check code style
3. **Build Docker Images** - Build service images
4. **Start Infrastructure** - Start databases and Redis
5. **Database Migrations** - Run Alembic migrations
6. **Unit Tests** - Run pytest unit tests
7. **Integration Tests** - Test API endpoints
8. **Feature Tests** - Test new enterprise features
9. **Security Tests** - Test security features
10. **Performance Tests** - Check service performance
11. **Build Artifacts** - Create deployment packages

## Manual Testing

### Pre-Deployment Tests

Run comprehensive tests before deploying:

```bash
# Run all tests
make test

# Or directly
./scripts/pre-deploy-test.sh
```

### CI Test Suite

Run CI test suite (simulates CI environment):

```bash
make test-ci

# Or directly
./scripts/ci-test.sh
```

### Individual Test Types

```bash
# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Linting
make lint

# Fix linting issues
make lint-fix
```

## Jenkins Configuration

### Required Plugins

The pipeline requires these Jenkins plugins (auto-installed via `jenkins/plugins.txt`):

- **Pipeline** - Core pipeline support
- **Docker Pipeline** - Docker integration
- **Git** - Git integration
- **Blue Ocean** - Modern UI
- **Email Extension** - Email notifications
- **JUnit** - Test reporting

### Environment Variables

Set these in Jenkins (Manage Jenkins → Configure System → Global Properties):

- `DOCKER_HOST` - Docker daemon socket
- `SMTP_HOST` - Email server (for notifications)
- `SMTP_USER` - Email username
- `SMTP_PASSWORD` - Email password

### Credentials

Add credentials in Jenkins (Manage Jenkins → Credentials):

- **Docker Hub** - For pushing images (if needed)
- **Git** - For private repositories
- **SSH** - For deployment (if needed)

## GitHub Actions

### Workflow Files

- `.github/workflows/ci.yml` - Main CI/CD pipeline

### Secrets

Add secrets in GitHub (Settings → Secrets):

- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password
- `DEPLOY_KEY` - SSH key for deployment

## Testing Features

### Password Strength Validation

```bash
# Should fail (weak password)
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"short","first_name":"Test","last_name":"User"}'

# Should succeed (strong password)
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"StrongPassword123!","first_name":"Test","last_name":"User"}'
```

### Rate Limiting

```bash
# Test rate limit (should get 429 after 5 attempts)
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"test@test.com","password":"wrong"}'
  sleep 0.5
done
```

### Device Fingerprinting

```bash
# Login with device info
TOKEN=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)' \
  -d '{"email":"test@test.com","password":"StrongPassword123!"}' \
  | jq -r '.access_token')

# Get sessions (should show device info)
curl -X GET http://localhost:8001/api/v1/auth/sessions/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

## Deployment

### Pre-Deployment Checklist

- [ ] All tests pass (`make test`)
- [ ] Code is linted (`make lint`)
- [ ] Migrations are up to date (`make migrate`)
- [ ] Environment variables are set
- [ ] Docker images are built
- [ ] Service health checks pass

### Deploy Command

```bash
# Run tests first
make test

# If tests pass, deploy
make deploy
```

### Deployment Steps

1. **Build and tag images:**
   ```bash
   docker-compose build
   docker tag quimicadealtura_api-auth-service:latest \
     quimicadealtura_api-auth-service:v1.0.0
   ```

2. **Push to registry** (if using):
   ```bash
   docker push quimicadealtura_api-auth-service:v1.0.0
   ```

3. **Update production:**
   ```bash
   # Update docker-compose.yml with new image tag
   docker-compose pull
   docker-compose up -d
   ```

## Troubleshooting

### Jenkins Issues

**Pipeline fails to start:**
- Check Docker socket permissions
- Verify Jenkins has access to Docker
- Check Jenkins logs: `docker logs jenkins`

**Tests fail in Jenkins:**
- Check service logs: `docker-compose logs auth-service`
- Verify database is accessible
- Check network connectivity

### GitHub Actions Issues

**Workflow doesn't run:**
- Check workflow file syntax
- Verify file is in `.github/workflows/`
- Check branch name matches trigger

**Tests fail in Actions:**
- Check service logs in Actions output
- Verify all services are healthy
- Check database connection

### General Issues

**Services don't start:**
```bash
# Check Docker
docker ps
docker-compose ps

# Check logs
docker-compose logs auth-service
docker-compose logs postgres-auth
docker-compose logs redis
```

**Migrations fail:**
```bash
# Check migration status
docker-compose exec auth-service alembic current

# Check database connection
docker-compose exec postgres-auth psql -U mp_auth_user -d medicinal_plants_auth
```

## Best Practices

1. **Always test before deploying** - Use `make test`
2. **Run linting** - Fix issues before committing
3. **Keep migrations up to date** - Run migrations in CI
4. **Monitor builds** - Set up notifications
5. **Use tags** - Tag Docker images with versions
6. **Document changes** - Update CHANGELOG.md
7. **Review logs** - Check CI/CD logs regularly

## Next Steps

1. **Set up monitoring** - Add Prometheus/Grafana
2. **Configure alerts** - Set up email/Slack notifications
3. **Add more tests** - Increase test coverage
4. **Automate deployment** - Set up auto-deploy on main branch
5. **Add staging environment** - Test before production
