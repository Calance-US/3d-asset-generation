# Keycloak SSO Setup Guide

This directory contains the Keycloak configuration for the 3D Educational Visualization Platform's single sign-on (SSO) authentication system.

## 🚀 Quick Start

### 1. Start Keycloak Server
```bash
# From the project root directory
./scripts/start-keycloak.sh
```

### 2. Access Admin Console
- **URL**: http://localhost:28080/admin
- **Username**: `admin`
- **Password**: `admin_password`

### 3. Test Login
Use any of the pre-configured test users:
- **admin@localhost.local** (admin role) - password: `password`
- **educator@localhost.local** (educator role) - password: `password`
- **student@localhost.local** (student role) - password: `password`

## 📁 Files Overview

```
keycloak/
├── README.md                # This documentation
├── realm-export.json        # Complete realm configuration
└── themes/                  # Custom themes (optional)
```

## 🔧 Configuration Details

### Realm: `local-apps`
- **Display Name**: Local Applications
- **User Registration**: Enabled
- **Login Theme**: Default Keycloak theme
- **Email Verification**: Disabled (for development)

### Client: `3d-visualization-app`
- **Client ID**: `3d-visualization-app`
- **Access Type**: Public (suitable for frontend applications)
- **Standard Flow**: Enabled (authorization code flow)
- **Valid Redirect URIs**:
  - `http://localhost:3000/*`
  - `http://localhost:3000/auth/callback`
  - `http://localhost:3000/silent-check-sso.html`
- **Web Origins**: `http://localhost:3000`

### Roles
- **admin**: Full system access and administrative privileges
- **educator**: Content creation and management privileges
- **student**: Basic content access (default role for new users)

### Protocol Mappers
The client includes standard OIDC mappers for:
- Username (`preferred_username`)
- Email (`email`)
- First/Last Name (`given_name`, `family_name`)
- Realm Roles (`realm_access.roles`)

## 🐳 Docker Configuration

### Services
- **keycloak**: Main Keycloak server (port 28080)
- **keycloak-db**: PostgreSQL database (port 5433)

### Volumes
- `keycloak_postgres_data`: Persistent database storage

### Environment Variables
Key environment variables are configured in `docker-compose.keycloak.yml`:
- `KEYCLOAK_ADMIN`: Admin username
- `KEYCLOAK_ADMIN_PASSWORD`: Admin password
- `KC_DB_*`: Database connection settings
- `KC_HOSTNAME_*`: Hostname and port configuration

## 🛠️ Management Commands

### Start Services
```bash
./scripts/start-keycloak.sh
```

### Stop Services
```bash
./scripts/stop-keycloak.sh
```

### View Logs
```bash
docker-compose -f docker-compose.keycloak.yml logs -f keycloak
```

### Restart Keycloak Only
```bash
docker-compose -f docker-compose.keycloak.yml restart keycloak
```

### Clean Reset (removes all data)
```bash
docker-compose -f docker-compose.keycloak.yml down -v
```

## 🔒 Security Configuration

### Development Mode
- HTTP is enabled for development
- Hostname verification is relaxed
- SSL is not required for external connections

### Production Considerations
For production deployment, ensure:
1. Enable HTTPS/SSL
2. Configure proper hostname verification
3. Use strong admin passwords
4. Enable email verification
5. Configure SMTP server for email notifications
6. Set up proper backup procedures

## 🧪 Testing Authentication Flow

### Manual Testing Steps
1. Start Keycloak: `./scripts/start-keycloak.sh`
2. Start your frontend: `cd frontend && npm start`
3. Start your backend: `cd backend && uv run python main.py`
4. Navigate to http://localhost:3000
5. Click login - should redirect to Keycloak
6. Login with test credentials
7. Should redirect back to application

### API Testing
Test token validation:
```bash
# Get token (replace with actual values)
curl -X POST http://localhost:28080/realms/local-apps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=3d-visualization-app&username=student@localhost.local&password=password"

# Use token to access protected API
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" http://localhost:8000/api/v1/history/
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check Docker daemon
docker info

# Check port conflicts
lsof -i :28080
lsof -i :5433

# View container logs
docker-compose -f docker-compose.keycloak.yml logs keycloak
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL container
docker exec keycloak-postgres pg_isready -U keycloak

# Connect to database
docker exec -it keycloak-postgres psql -U keycloak -d keycloak
```

#### 3. CORS Issues
Verify in Keycloak Admin Console:
- Client → Settings → Web Origins includes `http://localhost:3000`
- Valid Redirect URIs includes `http://localhost:3000/*`

#### 4. Token Validation Failures
- Check backend environment variables
- Verify Keycloak server URL in backend configuration
- Ensure realm name matches (`local-apps`)

### Log Locations
- **Keycloak**: `docker-compose -f docker-compose.keycloak.yml logs keycloak`
- **Database**: `docker-compose -f docker-compose.keycloak.yml logs keycloak-db`
- **Backend API**: Check your backend application logs
- **Frontend**: Browser developer console

## 📚 Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenID Connect Specification](https://openid.net/connect/)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## 🔄 Updating Configuration

### Modify Realm Settings
1. Access Admin Console: http://localhost:28080/admin
2. Select `local-apps` realm
3. Make changes via UI
4. Export updated configuration:
   ```bash
   # Export realm (replace container name if different)
   docker exec keycloak-server /opt/keycloak/bin/kc.sh export \
     --realm local-apps \
     --file /tmp/realm-export.json

   # Copy to host
   docker cp keycloak-server:/tmp/realm-export.json ./keycloak/realm-export.json
   ```

### Add New Users
Via Admin UI:
1. Go to Users → Add user
2. Set username, email, first/last name
3. Go to Credentials tab → Set password
4. Go to Role Mappings → Assign roles

### Add New Clients
Via Admin UI:
1. Go to Clients → Create
2. Set Client ID and protocol (openid-connect)
3. Configure access type and redirect URIs
4. Set up protocol mappers as needed

## 📝 Notes

- Default passwords are intentionally simple for development
- The realm configuration includes all necessary settings for the 3D visualization platform
- User sessions are configured with reasonable timeouts for development
- Registration is enabled for testing user creation flows
- All test users use the same password (`password`) for simplicity

---

**Last Updated**: June 2025
**Version**: 1.0.0
**Compatibility**: Keycloak 23.0+
