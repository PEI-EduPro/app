# Setup Keycloak Admin
# First, we need the admin token to create users and assign roles

> export ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')



# Create the 'manager' user
# Note: Keycloak returns 201 Created (empty body) on success

> curl -s -X POST http://localhost:8080/admin/realms/master/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "manager",
    "email": "manager@example.com",
    "firstName": "Manager",
    "lastName": "User",
    "enabled": true,
    "emailVerified": true,
    "credentials": [
      {
        "type": "password",
        "value": "manager123",
        "temporary": false
      }
    ]
  }' | jq



# Get the new User ID
# We need the UUID to assign roles

> export USER_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/master/users?username=manager" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')
> echo "User ID: $USER_ID"



# Get the 'manager' Role ID
# We need the UUID of the role to map it

> export ROLE_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/master/roles/manager" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')
> echo "Role ID: $ROLE_ID"



# Assign Role to User
# Maps the Role ID to the User ID

> curl -X POST "http://localhost:8080/admin/realms/master/users/$USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[
    {
      \"id\": \"$ROLE_ID\",
      \"name\": \"manager\"
    }
  ]" | jq



# Get Manager Token (Final Step)
# Login as the new manager using your backend client

> export MANAGER_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=manager" \
  -d "password=manager123" \
  -d "grant_type=password" \
  -d "client_id=api-backend" \
  -d "client_secret=**********" | jq -r '.access_token')


# Verify Manager Access (Optional)
# Check if the token works on your API

> curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $MANAGER_TOKEN" | jq