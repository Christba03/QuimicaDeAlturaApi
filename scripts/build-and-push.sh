#!/bin/bash

# Script to build Docker images and push commits
# Usage: ./scripts/build-and-push.sh [service-name]

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVICE="${1:-auth-service}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Build and Push${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build Docker image
echo -e "${GREEN}Building $SERVICE...${NC}"
docker compose build "$SERVICE"

echo ""
echo -e "${GREEN}✓ Build complete${NC}"
echo ""

# Commit and push
echo -e "${YELLOW}Proceeding to commit and push...${NC}"
./scripts/commit-and-push.sh

echo ""
echo -e "${GREEN}✅ All done!${NC}"
