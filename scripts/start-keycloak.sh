#!/bin/bash

# Keycloak Development Server Startup Script
# This script starts Keycloak server with PostgreSQL database for the 3D Visualization Platform

set -e

echo "🚀 Starting Keycloak Development Server..."
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

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

# Check if realm configuration exists
if [ ! -f "keycloak/realm-export.json" ]; then
    echo "❌ Error: keycloak/realm-export.json not found."
    echo "Please ensure the Keycloak realm configuration file exists."
    exit 1
fi

# Stop any existing containers
echo "🔄 Stopping existing Keycloak containers..."
$DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml down --remove-orphans

# Pull latest images
echo "📦 Pulling latest Docker images..."
$DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml pull

# Start the services
echo "🏗️  Starting Keycloak and PostgreSQL containers..."
$DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
until docker exec keycloak-postgres pg_isready -U keycloak > /dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo "❌ Error: PostgreSQL failed to start within $timeout seconds"
        echo "📋 Checking container logs..."
        $DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml logs keycloak-db
        exit 1
    fi
    counter=$((counter + 1))
    echo "   PostgreSQL not ready yet... ($counter/$timeout)"
    sleep 1
done

echo "✅ PostgreSQL is ready!"

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to be ready..."
timeout=60
counter=0
until curl -s http://localhost:28080/ | grep -q "Welcome to Keycloak" > /dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo "❌ Error: Keycloak failed to start within $timeout seconds"
        echo "📋 Checking container logs..."
        $DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml logs keycloak
        exit 1
    fi
    counter=$((counter + 1))
    echo "   Keycloak not ready yet... ($counter/$timeout)"
    sleep 2
done

echo "✅ Keycloak is ready!"

# Display connection information
echo ""
echo "🎉 Keycloak Development Server Started Successfully!"
echo "=================================================="
echo ""
echo "🌐 Keycloak Admin Console: http://localhost:28080/admin"
echo "👤 Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "🔧 Realm: local-apps"
echo "🏢 Client ID: 3d-visualization-app"
echo ""
echo "👥 Test Users:"
echo "   • Manual setup required via Admin Console"
echo "   • Create users with roles: admin, educator, student"
echo ""
echo "🔗 Application URLs:"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo ""
echo "📋 Useful Commands:"
echo "   • View logs: $DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml logs -f"
echo "   • Stop services: $DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml down"
echo "   • Restart: $DOCKER_COMPOSE_CMD -f docker-compose.keycloak.yml restart"
echo ""
echo "📚 Next Steps:"
echo "   1. Access Keycloak Admin Console to create realm and client"
echo "   2. Create realm: 'local-apps'"
echo "   3. Create client: '3d-visualization-app'"
echo "   4. Create test users with appropriate roles"
echo "   5. Start your frontend and backend applications"
echo ""

# Optionally open the admin console in browser (uncomment if desired)
# if command -v open &> /dev/null; then
#     echo "🌐 Opening Keycloak Admin Console in browser..."
#     open http://localhost:28080/admin
# elif command -v xdg-open &> /dev/null; then
#     echo "🌐 Opening Keycloak Admin Console in browser..."
#     xdg-open http://localhost:28080/admin
# fi

echo "✨ Keycloak setup complete! Happy coding! ✨"
