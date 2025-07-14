#!/bin/bash

# Seed Keycloak test users into the local Postgres users table
# Usage: Run after Keycloak setup and Alembic migrations
# This version uses docker-compose exec to run psql inside the running Postgres container.
# NOTE: POSTGRES_CONTAINER should be the Docker Compose service name, not the container name.

set -e

# --- Configuration ---
KEYCLOAK_URL="http://localhost:28080"
REALM_NAME="local-apps"
ADMIN_USER="admin"
ADMIN_PASSWORD="admin"

# Database connection (override with env vars if needed)
DB_NAME="${DB_NAME:-calance3dvisualizations}"
DB_USER="${DB_USER:-admin}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-postgres}"

# --- Prerequisite checks ---
if ! command -v jq >/dev/null 2>&1; then
    echo "[ERROR] jq is required but not installed. Please install jq."
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "[ERROR] docker-compose is required but not installed. Please install docker-compose."
    exit 1
fi

if ! docker-compose ps | grep -q "$POSTGRES_CONTAINER"; then
    echo "[ERROR] Postgres container (service) '$POSTGRES_CONTAINER' is not running. Please start it with 'docker-compose up -d'."
    exit 1
fi

# --- Get Keycloak admin access token ---
echo "[INFO] Getting Keycloak admin access token..."
ACCESS_TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -d "username=${ADMIN_USER}" \
    -d "password=${ADMIN_PASSWORD}" | jq -r '.access_token')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    echo "[ERROR] Failed to get Keycloak admin token"
    exit 1
fi

echo "[INFO] Got Keycloak admin token."

# --- Function to insert user into DB ---
insert_user() {
    local username="$1"
    local email="$2"
    local role="$3"
    local external_id="$4"
    local provider="$5"

    if [ "$external_id" = "FETCH_FROM_KEYCLOAK" ]; then
        echo "[INFO] Fetching UUID for user $username from Keycloak..."
        external_id=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
            "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users?username=${username}" | jq -r '.[0].id')
        if [ -z "$external_id" ] || [ "$external_id" = "null" ]; then
            echo "[ERROR] Failed to fetch UUID for user $username"
            return 1
        fi
    fi

    echo "[INFO] Inserting user $username with external_id $external_id and provider $provider into Postgres (via docker-compose exec)..."
    docker-compose exec -T "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<EOF
INSERT INTO users (external_id, provider, username, email, role, last_login, created_at, updated_at, is_deleted)
SELECT '$external_id', '$provider', '$username', '$email', '$role', NOW(), NOW(), NOW(), false
WHERE NOT EXISTS (SELECT 1 FROM users WHERE external_id = '$external_id');
EOF
}

# --- Insert all test users ---
# Keycloak users (fetch UUID from Keycloak)
insert_user "admin" "admin@localhost.local" "admin" "FETCH_FROM_KEYCLOAK" "keycloak"
insert_user "educator" "educator@localhost.local" "educator" "FETCH_FROM_KEYCLOAK" "keycloak"
insert_user "student" "student@localhost.local" "student" "FETCH_FROM_KEYCLOAK" "keycloak"
# System user for backend logic (hardcoded external_id)
insert_user "system" "system@localhost" "admin" "system-migration-user" "internal"

echo "[SUCCESS] User seeding complete." 