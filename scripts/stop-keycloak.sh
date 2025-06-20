#!/bin/bash

# Keycloak Development Server Stop Script
# This script stops Keycloak server and PostgreSQL database containers

set -e

echo "🛑 Stopping Keycloak Development Server..."
echo "========================================="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        echo "❌ Error: docker-compose or 'docker compose' command not found."
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "📁 Project directory: $PROJECT_ROOT"

# Check if the docker-compose file exists
if [ ! -f "docker-compose.keycloak.yml" ]; then
    echo "❌ Error: docker-compose.keycloak.yml not found in project root."
    echo "Please ensure the Docker Compose configuration file exists."
    exit 1
fi

# Stop and remove containers
echo "🔄 Stopping Keycloak containers..."
$DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml down --remove-orphans

# Optionally remove volumes (uncomment if you want to clear data)
# echo "🗑️  Removing volumes..."
# $DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml down -v

echo ""
echo "✅ Keycloak Development Server Stopped Successfully!"
echo "=================================================="
echo ""
echo "📋 Useful Commands:"
echo "   • Restart: ./scripts/start-keycloak.sh"
echo "   • Remove all data: $DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml down -v"
echo "   • View remaining containers: docker ps -a"
echo "   • Clean up Docker system: docker system prune"
echo ""
echo "💡 Note: Database data is preserved in Docker volumes."
echo "   Use 'docker-compose -f docker-compose.keycloak.yml down -v' to remove all data."
echo ""
echo "✨ Keycloak stopped successfully! ✨"
