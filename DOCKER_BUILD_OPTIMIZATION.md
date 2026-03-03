# Docker Build Optimization Guide

This guide explains how to optimize Docker builds for faster production deployments.

## Quick Start

### Enable BuildKit (Recommended)

```bash
# Enable BuildKit globally
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Or add to ~/.bashrc or ~/.zshrc
echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc
echo 'export COMPOSE_DOCKER_CLI_BUILD=1' >> ~/.bashrc
```

### Build with Optimizations

```bash
# Build all services with optimizations
make build-optimized

# Build production images
make build-prod

# Build specific service
make build-auth-prod
```

## Optimization Strategies

### 1. Multi-Stage Builds

The Dockerfiles use multi-stage builds to:
- **Base stage**: System dependencies (rarely changes)
- **Dependencies stage**: Python packages (changes when requirements.txt changes)
- **Production stage**: Application code (changes frequently)

This means:
- System dependencies are cached until base image changes
- Python packages are cached until requirements.txt changes
- Only application code needs rebuilding on each change

### 2. Layer Caching

Docker caches layers, so:
- Copy `requirements.txt` first (changes infrequently)
- Install dependencies (cached unless requirements.txt changes)
- Copy application code last (changes frequently)

### 3. BuildKit Cache Mounts

Production Dockerfiles use BuildKit cache mounts:
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

This caches pip downloads between builds, even if the layer is rebuilt.

### 4. .dockerignore

The `.dockerignore` file excludes:
- Git files
- Documentation
- Tests
- IDE files
- Build artifacts

This reduces build context size and speeds up builds.

## Build Commands

### Standard Build
```bash
docker compose build
```

### Optimized Build (BuildKit)
```bash
DOCKER_BUILDKIT=1 docker compose build
```

### Production Build
```bash
make build-prod
# Or
./scripts/build-optimized.sh all
```

### Build Specific Service
```bash
./scripts/build-optimized.sh auth-service
```

## Cache Management

### View Cache Statistics
```bash
make cache-stats
# Or
docker system df
docker builder du
```

### Save Cache
```bash
make cache-save
```

### Clear Cache (if needed)
```bash
make cache-clear
```

## Production Deployment

### Option 1: Build Locally, Push to Registry

```bash
# Build optimized images
make build-prod

# Tag for registry
docker tag quimicadealtura_api-auth-service:prod \
    registry.example.com/auth-service:v1.0.0

# Push to registry
docker push registry.example.com/auth-service:v1.0.0
```

### Option 2: Build on CI/CD

The Jenkinsfile and GitHub Actions workflows use optimized builds:

```groovy
// Jenkinsfile
environment {
    DOCKER_BUILDKIT = '1'
    COMPOSE_DOCKER_CLI_BUILD = '1'
}
```

### Option 3: Use Build Cache from Registry

```bash
# Build with cache from registry
docker build \
    --cache-from registry.example.com/auth-service:latest \
    --tag registry.example.com/auth-service:latest \
    services/auth-service
```

## Build Time Comparison

### Without Optimizations
- First build: ~5-10 minutes
- Rebuild (code change): ~3-5 minutes
- Rebuild (requirements change): ~5-10 minutes

### With Optimizations
- First build: ~5-10 minutes (same)
- Rebuild (code change): ~30-60 seconds ⚡
- Rebuild (requirements change): ~2-3 minutes ⚡

## Best Practices

### 1. Order Matters
```dockerfile
# ✅ Good: Copy requirements first
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# ❌ Bad: Copy everything first
COPY . .
RUN pip install -r requirements.txt
```

### 2. Use Specific Base Images
```dockerfile
# ✅ Good: Specific version
FROM python:3.11-slim

# ❌ Bad: Latest tag (unpredictable)
FROM python:latest
```

### 3. Minimize Layers
```dockerfile
# ✅ Good: Combine commands
RUN apt-get update && \
    apt-get install -y package && \
    rm -rf /var/lib/apt/lists/*

# ❌ Bad: Separate RUN commands
RUN apt-get update
RUN apt-get install -y package
RUN rm -rf /var/lib/apt/lists/*
```

### 4. Use .dockerignore
Always use `.dockerignore` to exclude unnecessary files:
- Reduces build context size
- Speeds up build
- Prevents sensitive files in image

### 5. Use Multi-Stage Builds
Separate build dependencies from runtime:
```dockerfile
FROM base as builder
RUN pip install build-tools

FROM base as production
COPY --from=builder /app/dist /app
```

## CI/CD Integration

### Jenkins

The Jenkinsfile automatically uses BuildKit:
```groovy
environment {
    DOCKER_BUILDKIT = '1'
    COMPOSE_DOCKER_CLI_BUILD = '1'
}
```

### GitHub Actions

GitHub Actions uses BuildKit by default in newer versions.

### GitLab CI

```yaml
variables:
  DOCKER_BUILDKIT: 1
  DOCKER_DRIVER: overlay2
```

## Troubleshooting

### Build Still Slow

1. **Check cache is being used:**
   ```bash
   docker builder du
   ```

2. **Verify BuildKit is enabled:**
   ```bash
   docker buildx version
   ```

3. **Check .dockerignore:**
   ```bash
   docker build --no-cache --progress=plain .
   ```

### Cache Not Working

1. **Clear and rebuild:**
   ```bash
   make cache-clear
   make build-optimized
   ```

2. **Check Docker version:**
   ```bash
   docker version
   # Need Docker 18.09+ for BuildKit
   ```

### Out of Disk Space

```bash
# Clean up build cache
docker builder prune -af

# Clean up unused images
docker image prune -af

# Clean up everything
docker system prune -af
```

## Advanced: Buildx with Remote Cache

For even faster builds, use remote cache:

```bash
docker buildx create --use --name builder
docker buildx build \
    --cache-from type=registry,ref=registry.example.com/auth-service:cache \
    --cache-to type=registry,ref=registry.example.com/auth-service:cache,mode=max \
    -t registry.example.com/auth-service:latest \
    --push \
    services/auth-service
```

## Summary

- ✅ Use multi-stage builds
- ✅ Enable BuildKit
- ✅ Use cache mounts
- ✅ Order layers correctly
- ✅ Use .dockerignore
- ✅ Build dependencies before code
- ✅ Use specific image tags
- ✅ Minimize layers

Following these practices can reduce build times by **80-90%** for code-only changes!
