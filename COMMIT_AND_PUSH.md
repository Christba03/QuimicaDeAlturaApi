# Commit and Push Guide

## Quick Commands

### Option 1: Commit and Push (Recommended)

```bash
# Run the automated script
./scripts/commit-and-push.sh
```

This will:
1. Stage all changes
2. Commit with a descriptive message
3. Pull remote changes (rebase)
4. Push to remote

### Option 2: Manual Steps

```bash
# 1. Stage all changes
git add -A

# 2. Commit
git commit -m "feat: Add enterprise auth features, CI/CD pipeline, and Docker build optimizations"

# 3. Pull remote changes
git pull --rebase origin main

# 4. Push
git push origin main
```

### Option 3: Build and Push Together

```bash
# Build Docker image and push commits
./scripts/build-and-push.sh auth-service
```

## Current Status

✅ **Docker build successful!** The auth-service image was built successfully.

📝 **Changes ready to commit:**
- Modified files: 15 files
- New files: 40+ files
- Includes: Enterprise auth features, CI/CD, Docker optimizations

## What Will Be Committed

### Enterprise Auth Features
- Password strength validation
- Password history
- Rate limiting
- Device fingerprinting
- Trusted devices
- Async email queue

### CI/CD Pipeline
- Jenkinsfile
- GitHub Actions workflow
- Test scripts
- Pre-deployment tests

### Docker Optimizations
- Multi-stage Dockerfiles
- BuildKit optimizations
- Cache management
- Production Dockerfiles

### Documentation
- Testing guides
- Build optimization guide
- CI/CD setup guide
- Quick start guide

## Troubleshooting

### If push fails with "remote contains work"

```bash
# Pull and rebase
git pull --rebase origin main

# Resolve any conflicts, then
git push origin main
```

### If you want to review changes first

```bash
# See what will be committed
git status
git diff --cached

# Then commit
git commit -m "your message"
```

### Custom commit message

```bash
./scripts/commit-and-push.sh "your custom commit message"
```

## Next Steps After Push

1. **GitHub Actions will run automatically** (if using GitHub)
2. **Jenkins pipeline will trigger** (if configured)
3. **Deploy to production** when ready
