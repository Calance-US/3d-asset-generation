#!/bin/bash

# Automated Keycloak Realm Setup Script
# This script configures Keycloak via REST API for the 3D Visualization Platform

set -e

echo "🔧 Setting up Keycloak realm and configuration..."
echo "================================================"

# Configuration variables
KEYCLOAK_URL="http://localhost:28080"
ADMIN_USER="admin"
ADMIN_PASSWORD="admin"
REALM_NAME="local-apps"
CLIENT_ID="3d-visualization-app"
FRONTEND_URL="http://localhost:3000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Keycloak is running
check_keycloak() {
    print_status "Checking if Keycloak is running..."
    if ! curl -s "${KEYCLOAK_URL}" > /dev/null 2>&1; then
        print_error "Keycloak is not running on ${KEYCLOAK_URL}"
        print_error "Please start Keycloak first: ./scripts/start-keycloak.sh"
        exit 1
    fi
    print_success "Keycloak is running"
}

# Function to get admin access token
get_admin_token() {
    print_status "Getting admin access token..."

    TOKEN_RESPONSE=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=password" \
        -d "client_id=admin-cli" \
        -d "username=${ADMIN_USER}" \
        -d "password=${ADMIN_PASSWORD}")

    if [ $? -ne 0 ] || [ -z "$TOKEN_RESPONSE" ]; then
        print_error "Failed to get admin token"
        exit 1
    fi

    ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty')

    if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
        print_error "Failed to parse access token from response"
        print_error "Response: $TOKEN_RESPONSE"
        exit 1
    fi

    print_success "Admin token obtained"
}

# Function to create realm
create_realm() {
    print_status "Creating realm: ${REALM_NAME}..."

    # Check if realm already exists
    REALM_CHECK=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}" \
        -w "%{http_code}" -o /dev/null)

    if [ "$REALM_CHECK" = "200" ]; then
        print_warning "Realm ${REALM_NAME} already exists, skipping creation"
        return
    fi

    REALM_CONFIG='{
        "realm": "'${REALM_NAME}'",
        "displayName": "Local Applications",
        "enabled": true,
        "registrationAllowed": true,
        "rememberMe": true,
        "verifyEmail": false,
        "loginWithEmailAllowed": true,
        "duplicateEmailsAllowed": false,
        "resetPasswordAllowed": true,
        "editUsernameAllowed": false,
        "sslRequired": "external",
        "defaultRoles": ["student"]
    }'

    RESPONSE=$(curl -s -X POST "${KEYCLOAK_URL}/admin/realms" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$REALM_CONFIG" \
        -w "%{http_code}")

    HTTP_CODE="${RESPONSE: -3}"

    if [ "$HTTP_CODE" = "201" ]; then
        print_success "Realm ${REALM_NAME} created successfully"
    else
        print_error "Failed to create realm. HTTP Code: ${HTTP_CODE}"
        exit 1
    fi
}

# Function to create roles
create_roles() {
    print_status "Creating realm roles..."

    ROLES=("admin:Administrator with full system access"
           "educator:Educator with content creation and management privileges"
           "student:Student with basic content access")

    for role_info in "${ROLES[@]}"; do
        IFS=':' read -r role_name role_description <<< "$role_info"

        print_status "Creating role: ${role_name}..."

        ROLE_CONFIG='{
            "name": "'${role_name}'",
            "description": "'${role_description}'",
            "composite": false,
            "clientRole": false
        }'

        RESPONSE=$(curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/roles" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "$ROLE_CONFIG" \
            -w "%{http_code}")

        HTTP_CODE="${RESPONSE: -3}"

        if [ "$HTTP_CODE" = "201" ]; then
            print_success "Role ${role_name} created"
        elif [ "$HTTP_CODE" = "409" ]; then
            print_warning "Role ${role_name} already exists"
        else
            print_error "Failed to create role ${role_name}. HTTP Code: ${HTTP_CODE}"
        fi
    done
}

# Function to set default role
set_default_role() {
    print_status "Setting student as default role..."

    # Get student role ID
    STUDENT_ROLE=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/roles/student")

    STUDENT_ROLE_ID=$(echo "$STUDENT_ROLE" | jq -r '.id // empty')

    if [ -z "$STUDENT_ROLE_ID" ]; then
        print_error "Failed to get student role ID"
        return
    fi

    DEFAULT_ROLE_CONFIG='[{
        "id": "'${STUDENT_ROLE_ID}'",
        "name": "student"
    }]'

    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/default-default-client-scopes" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$DEFAULT_ROLE_CONFIG" > /dev/null

    print_success "Default role configured"
}

# Function to create client
create_client() {
    print_status "Creating client: ${CLIENT_ID}..."

    CLIENT_CONFIG='{
        "clientId": "'${CLIENT_ID}'",
        "name": "3D Educational Visualization Platform",
        "description": "Frontend client for the 3D educational visualization platform",
        "enabled": true,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": ["'${FRONTEND_URL}'/*"],
        "webOrigins": ["'${FRONTEND_URL}'"],
        "publicClient": true,
        "standardFlowEnabled": true,
        "implicitFlowEnabled": false,
        "directAccessGrantsEnabled": true,
        "serviceAccountsEnabled": false,
        "protocol": "openid-connect",
        "fullScopeAllowed": true,
        "rootUrl": "'${FRONTEND_URL}'",
        "baseUrl": "'${FRONTEND_URL}'",
        "adminUrl": "'${FRONTEND_URL}'"
    }'

    RESPONSE=$(curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/clients" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$CLIENT_CONFIG" \
        -w "%{http_code}")

    HTTP_CODE="${RESPONSE: -3}"

    if [ "$HTTP_CODE" = "201" ]; then
        print_success "Client ${CLIENT_ID} created successfully"
    elif [ "$HTTP_CODE" = "409" ]; then
        print_warning "Client ${CLIENT_ID} already exists"
    else
        print_error "Failed to create client. HTTP Code: ${HTTP_CODE}"
        exit 1
    fi
}

# Function to create test users
create_test_users() {
    print_status "Creating test users..."

    USERS=("admin:admin@localhost.local:System:Administrator:admin"
           "educator:educator@localhost.local:Test:Educator:educator"
           "student:student@localhost.local:Test:Student:student")

    for user_info in "${USERS[@]}"; do
        IFS=':' read -r username email first_name last_name role <<< "$user_info"

        print_status "Creating user: ${username}..."

        USER_CONFIG='{
            "username": "'${username}'",
            "email": "'${email}'",
            "firstName": "'${first_name}'",
            "lastName": "'${last_name}'",
            "enabled": true,
            "emailVerified": true,
            "credentials": [{
                "type": "password",
                "value": "password",
                "temporary": false
            }]
        }'

        RESPONSE=$(curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "$USER_CONFIG" \
            -w "%{http_code}")

        HTTP_CODE="${RESPONSE: -3}"

        if [ "$HTTP_CODE" = "201" ]; then
            print_success "User ${username} created"

            # Get user ID for role assignment
            USER_RESPONSE=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
                "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users?username=${username}")

            USER_ID=$(echo "$USER_RESPONSE" | jq -r '.[0].id // empty')

            if [ -n "$USER_ID" ]; then
                # Get role ID
                ROLE_RESPONSE=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
                    "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/roles/${role}")

                ROLE_ID=$(echo "$ROLE_RESPONSE" | jq -r '.id // empty')

                if [ -n "$ROLE_ID" ]; then
                    # Assign role to user
                    ROLE_ASSIGNMENT='[{
                        "id": "'${ROLE_ID}'",
                        "name": "'${role}'"
                    }]'

                    curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users/${USER_ID}/role-mappings/realm" \
                        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
                        -H "Content-Type: application/json" \
                        -d "$ROLE_ASSIGNMENT" > /dev/null

                    print_success "Role ${role} assigned to user ${username}"
                fi
            fi

        elif [ "$HTTP_CODE" = "409" ]; then
            print_warning "User ${username} already exists"
        else
            print_error "Failed to create user ${username}. HTTP Code: ${HTTP_CODE}"
        fi
    done
}

# Function to test the setup
test_setup() {
    print_status "Testing authentication setup..."

    # Test token endpoint
    TEST_RESPONSE=$(curl -s -X POST "${KEYCLOAK_URL}/realms/${REALM_NAME}/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=password" \
        -d "client_id=${CLIENT_ID}" \
        -d "username=student" \
        -d "password=password" \
        -w "%{http_code}")

    HTTP_CODE="${TEST_RESPONSE: -3}"
    RESPONSE_BODY="${TEST_RESPONSE%???}"

    if [ "$HTTP_CODE" = "200" ]; then
        ACCESS_TOKEN_TEST=$(echo "$RESPONSE_BODY" | jq -r '.access_token // empty')
        if [ -n "$ACCESS_TOKEN_TEST" ] && [ "$ACCESS_TOKEN_TEST" != "null" ]; then
            print_success "Authentication test passed!"
        else
            print_warning "Authentication returned 200 but no valid token"
        fi
    else
        print_error "Authentication test failed. HTTP Code: ${HTTP_CODE}"
        print_error "Response: ${RESPONSE_BODY}"
    fi
}

# Main execution
main() {
    echo "Starting Keycloak setup for 3D Visualization Platform"
    echo "====================================================="

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Please install jq first:"
        print_error "  macOS: brew install jq"
        print_error "  Ubuntu/Debian: sudo apt-get install jq"
        print_error "  CentOS/RHEL: sudo yum install jq"
        exit 1
    fi

    check_keycloak
    get_admin_token
    create_realm
    create_roles
    set_default_role
    create_client
    create_test_users
    test_setup

    echo ""
    print_success "🎉 Keycloak setup completed successfully!"
    echo ""
    echo "📋 Configuration Summary:"
    echo "========================="
    echo "🌐 Keycloak URL: ${KEYCLOAK_URL}"
    echo "🏢 Realm: ${REALM_NAME}"
    echo "🔑 Client ID: ${CLIENT_ID}"
    echo "👥 Test Users (password: 'password'):"
    echo "   • admin@localhost.local (admin role)"
    echo "   • educator@localhost.local (educator role)"
    echo "   • student@localhost.local (student role)"
    echo ""
    echo "🧪 Test Authentication:"
    echo "curl -X POST '${KEYCLOAK_URL}/realms/${REALM_NAME}/protocol/openid-connect/token' \\"
    echo "  -H 'Content-Type: application/x-www-form-urlencoded' \\"
    echo "  -d 'grant_type=password&client_id=${CLIENT_ID}&username=student&password=password'"
    echo ""
    echo "🔗 Frontend Auth URL:"
    echo "${KEYCLOAK_URL}/realms/${REALM_NAME}/protocol/openid-connect/auth?client_id=${CLIENT_ID}&redirect_uri=${FRONTEND_URL}&response_type=code&scope=openid"
    echo ""
    print_success "You can now test your frontend authentication!"
}

# Run main function
main "$@"
