#!/bin/bash

# Script to commit changes and push to remote
# Usage: ./scripts/commit-and-push.sh [commit-message]

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

COMMIT_MSG="${1:-feat: Add enterprise auth features, CI/CD pipeline, and Docker build optimizations

- Add password strength validation with zxcvbn
- Implement password history enforcement
- Add Redis-based rate limiting
- Implement device fingerprinting and trusted devices
- Add async email queue with ARQ
- Set up Jenkins CI/CD pipeline
- Add GitHub Actions workflow
- Optimize Docker builds with multi-stage builds and BuildKit
- Add comprehensive testing scripts and documentation
- Resolve Redis port conflicts
- Merge Makefile functionality}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Git Commit and Push${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Check current branch
BRANCH=$(git branch --show-current)
echo -e "${GREEN}Current branch: $BRANCH${NC}"
echo ""

# Show status
echo "Changes to be committed:"
git status --short
echo ""

# Ask for confirmation
read -p "Continue with commit and push? (y/N): " confirm
if [ "$confirm" != "y" ]; then
    echo "Cancelled"
    exit 0
fi

# Stage all changes
echo -e "${YELLOW}Staging changes...${NC}"
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo -e "${YELLOW}No changes to commit${NC}"
    exit 0
fi

# Commit
echo -e "${YELLOW}Committing changes...${NC}"
git commit -m "$COMMIT_MSG"

# Pull first to merge any remote changes
echo -e "${YELLOW}Pulling remote changes...${NC}"
git pull --rebase origin "$BRANCH" || {
    echo -e "${RED}Pull failed. Resolve conflicts and try again.${NC}"
    exit 1
}

# Push
echo -e "${YELLOW}Pushing to remote...${NC}"
git push origin "$BRANCH"

echo ""
echo -e "${GREEN}✅ Successfully committed and pushed!${NC}"
echo ""
echo "Commit hash: $(git rev-parse --short HEAD)"
echo "Remote: $(git remote get-url origin)"
