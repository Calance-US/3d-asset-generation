# Keycloak Manual Setup Guide

This guide will walk you through setting up Keycloak manually for the 3D Educational Visualization Platform.

## 🚀 Prerequisites

1. Keycloak server running on http://localhost:28080
2. Admin credentials: `admin` / `admin_password`

## 📋 Step-by-Step Setup

### Step 1: Access Admin Console

1. Open your browser and go to: http://localhost:28080/admin
2. Login with:
   - **Username**: `admin`
   - **Password**: `admin_password`

### Step 2: Create Realm

1. In the top-left corner, click on "Master" dropdown
2. Click "Create Realm"
3. Enter the following details:
   - **Realm name**: `local-apps`
   - **Display name**: `Local Applications`
   - **Enabled**: ✅ (checked)
4. Click "Create"

### Step 3: Configure Realm Settings

1. In the left sidebar, click "Realm settings"
2. Go to the "Login" tab
3. Configure the following settings:
   - **User registration**: ✅ Enabled
   - **Forgot password**: ✅ Enabled
   - **Remember me**: ✅ Enabled
   - **Login with email**: ✅ Enabled
4. Click "Save"

### Step 4: Create Client

1. In the left sidebar, click "Clients"
2. Click "Create client"
3. **General Settings**:
   - **Client type**: OpenID Connect
   - **Client ID**: `3d-visualization-app`
   - **Name**: `3D Educational Visualization Platform`
   - **Description**: `Frontend client for the 3D educational visualization platform`
4. Click "Next"

5. **Capability config**:
   - **Client authentication**: OFF (public client)
   - **Authorization**: OFF
   - **Standard flow**: ✅ Enabled
   - **Direct access grants**: ✅ Enabled
6. Click "Next"

7. **Login settings**:
   - **Root URL**: `http://localhost:3000`
   - **Home URL**: `http://localhost:3000`
   - **Valid redirect URIs**: `http://localhost:3000/*`
   - **Valid post logout redirect URIs**: `http://localhost:3000`
   - **Web origins**: `http://localhost:3000`
8. Click "Save"

### Step 5: Create Roles

1. In the left sidebar, click "Realm roles"
2. Click "Create role"
3. Create the following roles one by one:

#### Admin Role
- **Role name**: `admin`
- **Description**: `Administrator with full system access`
- Click "Save"

#### Educator Role
- **Role name**: `educator`
- **Description**: `Educator with content creation and management privileges`
- Click "Save"

#### Student Role
- **Role name**: `student`
- **Description**: `Student with basic content access`
- Click "Save"

### Step 6: Set Default Role

1. In "Realm roles", click on the "Default roles" tab
2. Click "Assign role"
3. Select `student` role
4. Click "Assign"

### Step 7: Create Test Users

Create the following test users:

#### Admin User
1. Go to "Users" → "Create new user"
2. Fill in:
   - **Username**: `admin`
   - **Email**: `admin@localhost.local`
   - **First name**: `System`
   - **Last name**: `Administrator`
   - **Email verified**: ✅ Enabled
   - **Enabled**: ✅ Enabled
3. Click "Create"
4. Go to "Credentials" tab
5. Click "Set password"
   - **Password**: `password`
   - **Temporary**: OFF
6. Click "Save"
7. Go to "Role mapping" tab
8. Click "Assign role"
9. Select `admin` role and click "Assign"

#### Educator User
1. Go to "Users" → "Create new user"
2. Fill in:
   - **Username**: `educator`
   - **Email**: `educator@localhost.local`
   - **First name**: `Test`
   - **Last name**: `Educator`
   - **Email verified**: ✅ Enabled
   - **Enabled**: ✅ Enabled
3. Click "Create"
4. Set password to `password` (same process as admin)
5. Assign `educator` role

#### Student User
1. Go to "Users" → "Create new user"
2. Fill in:
   - **Username**: `student`
   - **Email**: `student@localhost.local`
   - **First name**: `Test`
   - **Last name**: `Student`
   - **Email verified**: ✅ Enabled
   - **Enabled**: ✅ Enabled
3. Click "Create"
4. Set password to `password` (same process as admin)
5. Assign `student` role (should already be assigned as default)

## 🧪 Testing the Setup

### Test 1: Direct Authentication

1. Open a new browser tab
2. Go to: http://localhost:28080/realms/local-apps/account
3. Try logging in with:
   - Username: `admin` / Password: `password`
   - Username: `educator` / Password: `password`
   - Username: `student` / Password: `password`

### Test 2: Token Endpoint

Test the token endpoint with curl:

```bash
curl -X POST http://localhost:28080/realms/local-apps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=3d-visualization-app&username=student&password=password"
```

You should receive a JSON response with access_token, refresh_token, etc.

### Test 3: Frontend Integration

1. Start your frontend application: `cd frontend && npm start`
2. Navigate to http://localhost:3000
3. Click login - should redirect to Keycloak
4. Login with test credentials
5. Should redirect back to application with authentication

## 🔧 Configuration Summary

After completing this setup, your Keycloak will have:

- **Realm**: `local-apps`
- **Client**: `3d-visualization-app` (public, standard flow enabled)
- **Roles**: `admin`, `educator`, `student` (student is default)
- **Test Users**: admin, educator, student (all with password: `password`)
- **Valid URLs**: http://localhost:3000/*

## 🐛 Troubleshooting

### Issue: "Invalid redirect URI"
- Check that "Valid redirect URIs" in client settings includes `http://localhost:3000/*`
- Ensure "Web origins" includes `http://localhost:3000`

### Issue: "Client not found"
- Verify client ID is exactly `3d-visualization-app`
- Ensure you're using the correct realm (`local-apps`)

### Issue: CORS errors
- Check "Web origins" setting in client configuration
- Ensure your frontend is running on http://localhost:3000

### Issue: Token validation fails
- Verify your backend is configured to use:
  - Keycloak URL: `http://localhost:28080`
  - Realm: `local-apps`
  - Client ID: `3d-visualization-app`

## 📱 Environment Variables

After setup, ensure your applications use these environment variables:

### Backend (.env)
```
KEYCLOAK_SERVER_URL=http://localhost:28080
KEYCLOAK_REALM=local-apps
KEYCLOAK_CLIENT_ID=3d-visualization-app
```

### Frontend (.env)
```
REACT_APP_KEYCLOAK_URL=http://localhost:28080
REACT_APP_KEYCLOAK_REALM=local-apps
REACT_APP_KEYCLOAK_CLIENT_ID=3d-visualization-app
```

## ✅ Verification Checklist

- [ ] Keycloak server running on port 28080
- [ ] Realm `local-apps` created
- [ ] Client `3d-visualization-app` configured with correct URLs
- [ ] Roles `admin`, `educator`, `student` created
- [ ] `student` set as default role
- [ ] Test users created with correct roles
- [ ] Token endpoint returns valid tokens
- [ ] Frontend can authenticate via Keycloak
- [ ] Backend can validate tokens

---

**Setup Complete!** 🎉

Your Keycloak server is now configured for the 3D Educational Visualization Platform. You can now test the full authentication flow between your frontend, backend, and Keycloak.
