#!/bin/bash

# Optimized build script for production
# Uses BuildKit, cache mounts, and layer caching

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Optimized Docker Build${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build options
SERVICE="${1:-all}"
PUSH="${2:-false}"
TAG="${3:-latest}"

echo "Building with optimizations:"
echo "  - BuildKit enabled"
echo "  - Cache mounts"
echo "  - Layer caching"
echo "  - Multi-stage builds"
echo ""

build_service() {
    local service=$1
    local context="./services/$service"
    
    if [ ! -d "$context" ]; then
        echo "Service $service not found, skipping..."
        return
    fi
    
    echo -e "${GREEN}Building $service...${NC}"
    
    # Check if production Dockerfile exists
    if [ -f "$context/Dockerfile.prod" ]; then
        docker build \
            --file "$context/Dockerfile.prod" \
            --tag "quimicadealtura_api-$service:$TAG" \
            --tag "quimicadealtura_api-$service:latest" \
            --cache-from "quimicadealtura_api-$service:latest" \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            "$context"
    else
        docker build \
            --tag "quimicadealtura_api-$service:$TAG" \
            --tag "quimicadealtura_api-$service:latest" \
            --cache-from "quimicadealtura_api-$service:latest" \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            "$context"
    fi
    
    echo -e "${GREEN}✓ $service built${NC}"
    echo ""
}

if [ "$SERVICE" == "all" ]; then
    echo "Building all services..."
    echo ""
    
    # Build in dependency order
    build_service "auth-service"
    build_service "plant-service"
    build_service "chatbot-service"
    build_service "search-service"
    build_service "user-service"
    build_service "api-gateway"
    
    echo -e "${GREEN}All services built successfully!${NC}"
else
    build_service "$SERVICE"
fi

# Push to registry if requested
if [ "$PUSH" == "push" ]; then
    echo "Pushing images to registry..."
    docker push "quimicadealtura_api-$SERVICE:$TAG"
fi

echo ""
echo "Build complete!"
echo ""
echo "To use optimized builds:"
echo "  export DOCKER_BUILDKIT=1"
echo "  docker-compose -f docker-compose.yml -f docker-compose.build.yml build"
