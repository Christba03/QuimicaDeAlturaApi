#!/bin/bash

# Build cache management script
# Helps manage Docker build cache for faster builds

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

case "${1:-help}" in
    save)
        echo -e "${YELLOW}Saving build cache...${NC}"
        docker buildx prune --filter "until=168h" --keep-storage 10GB
        echo -e "${GREEN}✓ Cache saved${NC}"
        ;;
    
    load)
        echo -e "${YELLOW}Loading build cache...${NC}"
        # Cache is automatically used by BuildKit
        echo -e "${GREEN}✓ Cache will be used on next build${NC}"
        ;;
    
    clear)
        echo -e "${YELLOW}Clearing build cache...${NC}"
        read -p "Are you sure? This will slow down builds (y/N): " confirm
        if [ "$confirm" == "y" ]; then
            docker builder prune -af
            echo -e "${GREEN}✓ Cache cleared${NC}"
        else
            echo "Cancelled"
        fi
        ;;
    
    stats)
        echo -e "${YELLOW}Build cache statistics:${NC}"
        docker system df
        echo ""
        echo "Build cache:"
        docker builder du
        ;;
    
    *)
        echo "Usage: $0 {save|load|clear|stats}"
        echo ""
        echo "Commands:"
        echo "  save   - Save and optimize build cache"
        echo "  load   - Prepare cache for use (automatic with BuildKit)"
        echo "  clear  - Clear all build cache"
        echo "  stats  - Show cache statistics"
        exit 1
        ;;
esac
