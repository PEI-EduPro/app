# Keycloak Cheat Sheet

## 🚀 Quick Start

### Docker Run
```bash
docker run -d \
  --name keycloak \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  -p 8080:8080 \
  quay.io/keycloak/keycloak:24.0.1 start-dev
```

### Access Admin Console
- **URL**: http://localhost:8080
- **Username**: `admin`
- **Password**: `admin`

## 📋 Core Concepts

### 1. **Realms**
- Isolated security domains
- Each realm has separate users, clients, roles
- **Master Realm**: Default admin realm
- **Create New**: Admin Console → Realm dropdown → Create Realm

### 2. **Clients**
- Applications that can request authentication
- **Types**: 
  - `openid-connect` (web/mobile apps)
  - `saml` (enterprise SSO)
- **Client Settings**:
  - `Client ID`: Unique identifier
  - `Client Protocol`: openid-connect
  - `Access Type`: public/confidential/bearer-only

### 3. **Users & Authentication**
- **User Management**: Users → Add User
- **Credentials**: Users → User → Credentials tab
- **Required Actions**: Force password change, email verification

### 4. **Roles & Groups**
- **Realm Roles**: Apply to entire realm
- **Client Roles**: Specific to client
- **Groups**: Organize users, assign roles in bulk
- **Composite Roles**: Roles that contain other roles

## ⚙️ Common Configurations

### Client Setup
```bash
# 1. Create Client
Clients → Create
Client ID: "your-app"
Client Protocol: openid-connect

# 2. Configure
Access Type: confidential
Valid Redirect URIs: http://localhost:3000/*
Web Origins: http://localhost:3000

# 3. Get Credentials
Clients → your-app → Credentials tab
Copy "Client Secret"
```

### User Creation
```bash
# 1. Create User
Users → Add User
Username: "user1"
Email: "user1@example.com"
First/Last Name: Optional

# 2. Set Password
Users → user1 → Credentials tab
Set Password (Turn OFF "Temporary")

# 3. Assign Roles
Users → user1 → Role Mappings
Assign realm roles
```

## 🔑 Authentication Flows

### Standard OIDC Flow
1. **Authorization Endpoint**: `/protocol/openid-connect/auth`
2. **Token Endpoint**: `/protocol/openid-connect/token`
3. **UserInfo Endpoint**: `/protocol/openid-connect/userinfo`
4. **Logout Endpoint**: `/protocol/openid-connect/logout`

### Get Token (Password Grant)
```bash
curl -X POST http://localhost:8080/realms/your-realm/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1" \
  -d "password=password" \
  -d "grant_type=password" \
  -d "client_id=your-app" \
  -d "client_secret=your-client-secret"
```

### Get Token (Client Credentials)
```bash
curl -X POST http://localhost:8080/realms/your-realm/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=your-app" \
  -d "client_secret=your-client-secret"
```

## 🔧 Important Endpoints

### Discovery Endpoint
```
GET /realms/{realm}/.well-known/openid-configuration
```

### Token Introspection
```bash
curl -X POST http://localhost:8080/realms/your-realm/protocol/openid-connect/token/introspect \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=your-token" \
  -d "client_id=your-app" \
  -d "client_secret=your-client-secret"
```

### User Info
```bash
curl -X GET http://localhost:8080/realms/your-realm/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer your-token"
```

## 🛡️ Security Configurations

### Password Policy
```
Realm Settings → Authentication → Password Policy
- Length (e.g., minimum 8 characters)
- Digits (require numbers)
- Special characters
- Not username
```

### Session Management
```
Realm Settings → Tokens
- SSO Session Max: 10 hours
- Access Token Lifespan: 5 minutes
- Refresh Token Lifespan: 30 days
```

### CORS Configuration
```
Clients → your-app → Web Origins
- Add allowed origins: http://localhost:3000
- Or use "+" for all origins
```

## 👥 User Management

### Bulk Operations
```bash
# Export Users
Realm Settings → Action → Partial Export

# Import Users
Realm Settings → Action → Partial Import
```

### User Attributes
```
Users → user1 → Attributes
- Add custom attributes: department, phone, etc.
```

### Groups & Role Mapping
```
Groups → Create Group
- Assign roles to group
- Add users to group (automatic role assignment)
```

## 🔄 Identity Providers

### Social Logins
```
Identity Providers → Add Provider
- Google, GitHub, Facebook, etc.
- Requires OAuth2 credentials from provider
```

### LDAP/Active Directory
```
User Federation → Add Provider → LDAP
- Configure connection to corporate directory
- Sync users and groups
```

## 📊 Monitoring & Logging

### Event Logging
```
Realm Settings → Events
- Enable Login, Logout events
- Configure event listeners
```

### Admin Events
```
Realm Settings → Events → Admin Events
- Log configuration changes
- Audit trail for admin actions
```

## 🐳 Docker & Production

### Production Docker
```bash
docker run -d \
  --name keycloak \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=secure-password \
  -e KC_DB=postgres \
  -e KC_DB_URL_HOST=postgres \
  -e KC_DB_URL_DATABASE=keycloak \
  -e KC_DB_USERNAME=keycloak \
  -e KC_DB_PASSWORD=db-password \
  -p 8080:8080 \
  quay.io/keycloak/keycloak:24.0.1 start
```

### Health Checks
```bash
# Health endpoint
curl http://localhost:8080/health/ready

# Metrics (if enabled)
curl http://localhost:8080/metrics
```

## 🚨 Troubleshooting

### Common Issues

1. **"Invalid client credentials"**
   - Check client secret
   - Verify client exists in correct realm

2. **"User not found"** 
   - Check realm
   - Verify user is enabled
   - Check username spelling

3. **"Invalid redirect URI"**
   - Add URI to Valid Redirect URIs in client config

4. **Token validation fails**
   - Check realm public key
   - Verify token hasn't expired

### Debug Mode
```bash
# Start with debug logging
docker run ... quay.io/keycloak/keycloak:24.0.1 start --verbose

# Check logs
docker logs keycloak-container
```

## 📝 Quick Commands Reference

### Realm Operations
- **Create Realm**: Admin Console → Realm dropdown → Create
- **Export Realm**: Realm Settings → Action → Export
- **Import Realm**: Add Realm → Import

### User Operations
- **Create User**: Users → Add User
- **Reset Password**: Users → User → Credentials → Reset Password
- **Assign Roles**: Users → User → Role Mappings

### Client Operations
- **Create Client**: Clients → Create
- **Get Secret**: Clients → Client → Credentials
- **Configure Roles**: Clients → Client → Roles

This cheat sheet covers the essential Keycloak operations and configurations for daily use!