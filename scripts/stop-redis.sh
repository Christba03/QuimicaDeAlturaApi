#!/bin/bash

# Quick script to stop Redis processes/containers using port 6379

set -e

echo "Stopping Redis processes..."

# Stop Docker Redis containers
if command -v docker &> /dev/null; then
    echo "Checking for Docker Redis containers..."
    DOCKER_REDIS=$(docker ps -a --filter "name=redis" --format "{{.Names}}" 2>/dev/null || echo "")
    if [ ! -z "$DOCKER_REDIS" ]; then
        echo "Stopping: $DOCKER_REDIS"
        docker stop $DOCKER_REDIS 2>/dev/null || true
        docker rm $DOCKER_REDIS 2>/dev/null || true
        echo "✓ Docker Redis containers stopped"
    fi
fi

# Stop systemd Redis service
if systemctl is-active --quiet redis 2>/dev/null; then
    echo "Stopping systemd Redis service..."
    sudo systemctl stop redis
    echo "✓ Redis service stopped"
elif systemctl is-active --quiet redis-server 2>/dev/null; then
    echo "Stopping systemd Redis server..."
    sudo systemctl stop redis-server
    echo "✓ Redis server stopped"
fi

# Kill processes on port 6379
REDIS_PID=$(lsof -ti :6379 2>/dev/null || echo "")
if [ ! -z "$REDIS_PID" ]; then
    echo "Killing process on port 6379 (PID: $REDIS_PID)..."
    sudo kill $REDIS_PID 2>/dev/null || true
    echo "✓ Process killed"
fi

echo ""
echo "Done! Port 6379 should now be available."
