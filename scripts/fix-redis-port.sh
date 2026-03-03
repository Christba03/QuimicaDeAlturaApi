#!/bin/bash

# Script to fix Redis port conflict
# This script helps resolve port 6379 conflicts

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Redis Port Conflict Resolution${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if port 6379 is in use
if lsof -i :6379 > /dev/null 2>&1 || ss -tuln | grep -q ":6379"; then
    echo -e "${YELLOW}Port 6379 is already in use${NC}"
    echo ""
    
    # Check for Docker containers
    echo "Checking for Docker Redis containers..."
    DOCKER_REDIS=$(docker ps -a --filter "name=redis" --format "{{.Names}}" 2>/dev/null || echo "")
    
    if [ ! -z "$DOCKER_REDIS" ]; then
        echo -e "${GREEN}Found Docker Redis containers:${NC}"
        echo "$DOCKER_REDIS"
        echo ""
        echo "Options:"
        echo "  1. Stop existing Docker Redis containers"
        echo "  2. Use different port (6380) for new Redis"
        echo ""
        read -p "Choose option (1 or 2): " choice
        
        if [ "$choice" == "1" ]; then
            echo "Stopping existing Redis containers..."
            docker stop $(docker ps -a --filter "name=redis" --format "{{.Names}}") 2>/dev/null || true
            docker rm $(docker ps -a --filter "name=redis" --format "{{.Names}}") 2>/dev/null || true
            echo -e "${GREEN}✓ Redis containers stopped${NC}"
        fi
    else
        # Check for local Redis process
        REDIS_PID=$(lsof -ti :6379 2>/dev/null || ss -tuln | grep ":6379" | awk '{print $NF}' | cut -d: -f1 || echo "")
        
        if [ ! -z "$REDIS_PID" ]; then
            echo -e "${YELLOW}Found Redis process using port 6379${NC}"
            echo ""
            echo "Options:"
            echo "  1. Stop local Redis process"
            echo "  2. Use different port (6380) for Docker Redis"
            echo ""
            read -p "Choose option (1 or 2): " choice
            
            if [ "$choice" == "1" ]; then
                echo "Stopping local Redis..."
                sudo systemctl stop redis 2>/dev/null || \
                sudo systemctl stop redis-server 2>/dev/null || \
                sudo kill $REDIS_PID 2>/dev/null || \
                echo "Could not stop Redis automatically. Please stop it manually."
            fi
        else
            echo -e "${YELLOW}Port 6379 is in use but couldn't identify the process${NC}"
            echo "You can either:"
            echo "  1. Stop the process using port 6379 manually"
            echo "  2. Use a different port for Docker Redis (6380)"
            echo ""
            echo "To use a different port, set REDIS_PORT environment variable:"
            echo "  export REDIS_PORT=6380"
            echo "  docker-compose up -d redis"
        fi
    fi
else
    echo -e "${GREEN}✓ Port 6379 is available${NC}"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
