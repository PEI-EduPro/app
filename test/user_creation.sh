#!/bin/bash

echo "=== Complete User Authentication Test (Keycloak-Centric) ==="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

CLIENT_SECRET="RdwcPv5Gp0Nq3Pm8fGV4HfpST4KurVhb"

# Step 1: Get Admin Token (to create user in Keycloak)
echo -e "\n${YELLOW}1. Getting Admin Token...${NC}"
ADMIN_TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=admin-cli")

echo "Raw Admin Token Response:"
echo "$ADMIN_TOKEN_RESPONSE" | jq .
echo

ADMIN_TOKEN=$(echo "$ADMIN_TOKEN_RESPONSE" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" != "null" ] && [ -n "$ADMIN_TOKEN" ] && [ "$ADMIN_TOKEN" != "null" ]; then
    echo -e "${GREEN}✓ Admin token obtained${NC}"
    echo "Admin Token (first 100 chars): ${ADMIN_TOKEN:0:100}..."
else
    echo -e "${RED}✗ Failed to get admin token${NC}"
    exit 1
fi

# Step 2: Create New User in Keycloak
echo -e "\n${YELLOW}2. Creating New User in Keycloak...${NC}"
USER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8080/admin/realms/EduPro/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newstudent",
    "email": "newstudent@example.com",
    "firstName": "New",
    "lastName": "Student",
    "enabled": true,
    "emailVerified": true,
    "credentials": [
      {
        "type": "password",
        "value": "newpassword123",
        "temporary": false
      }
    ]
  }')

HTTP_CODE=$(echo "$USER_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$USER_RESPONSE" | head -n1)

echo "HTTP Status: $HTTP_CODE"
echo "Response Body: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "201" ]; then
    echo -e "${GREEN}✓ User created successfully in Keycloak${NC}"
    USER_LOCATION=$(echo "$USER_RESPONSE" | head -n1 | grep -o '[^/]*$')
    echo "Created User ID: $USER_LOCATION"
else
    echo -e "${RED}✗ User creation failed in Keycloak (HTTP $HTTP_CODE)${NC}"
    if [ "$HTTP_CODE" = "409" ]; then
        echo "Note: User might already exist (HTTP 409). This is okay for testing authentication flow."
        EXISTING_USER_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/EduPro/users?username=newstudent" \
          -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')
        if [ -n "$EXISTING_USER_ID" ] && [ "$EXISTING_USER_ID" != "null" ]; then
             USER_LOCATION=$EXISTING_USER_ID
             echo "Found existing user ID: $EXISTING_USER_ID"
        else
             echo "Could not find existing user ID."
             exit 1
        fi
    else
        exit 1
    fi
fi

# Step 2.5: Assign 'student' role
echo -e "\n${YELLOW}2.5. Assigning 'student' role to user in Keycloak...${NC}"
ROLE_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/EduPro/roles/student" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

if [ -n "$ROLE_ID" ] && [ "$ROLE_ID" != "null" ]; then
    ASSIGN_ROLE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:8080/admin/realms/EduPro/users/$USER_LOCATION/role-mappings/realm" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      --data "[{\"id\":\"$ROLE_ID\",\"name\":\"student\"}]")

    ASSIGN_HTTP_CODE=$(echo "$ASSIGN_ROLE_RESPONSE" | tail -n1)
    if [ "$ASSIGN_HTTP_CODE" = "204" ]; then
        echo -e "${GREEN}✓ 'student' role assigned successfully${NC}"
    else
        echo -e "${RED}✗ Failed to assign 'student' role (HTTP $ASSIGN_HTTP_CODE)${NC}"
        echo "Role Assignment Response: $(echo "$ASSIGN_ROLE_RESPONSE" | head -n1)"
    fi
else
    echo -e "${RED}✗ Could not find 'student' role ID${NC}"
fi

# Step 3: Get Token as New User from Keycloak
echo -e "\n${YELLOW}3. Getting Token as New User from Keycloak...${NC}"
USER_TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/realms/EduPro/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=newstudent" \
  -d "password=newpassword123" \
  -d "grant_type=password" \
  -d "client_id=api-backend" \
  -d "client_secret=$CLIENT_SECRET")

echo "Raw User Token Response:"
echo "$USER_TOKEN_RESPONSE" | jq .
echo

USER_TOKEN=$(echo "$USER_TOKEN_RESPONSE" | jq -r '.access_token')

if [ "$USER_TOKEN" != "null" ] && [ -n "$USER_TOKEN" ]; then
    echo -e "${GREEN}✓ User token obtained successfully from Keycloak${NC}"
    echo "User Token (full): $USER_TOKEN"
    echo "User Token (first 100 chars): ${USER_TOKEN:0:100}..."
else
    echo -e "${RED}✗ Failed to get user token from Keycloak${NC}"
    exit 1
fi

# Step 4: Test API Access to /me endpoint
echo -e "\n${YELLOW}4. Testing API Access to /me endpoint...${NC}"
echo "Using token: ${USER_TOKEN:0:50}..."
echo

API_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json")

API_HTTP_CODE=$(echo "$API_RESPONSE" | tail -n1)
API_BODY=$(echo "$API_RODY" | head -n1)

echo "API Response HTTP Code: $API_HTTP_CODE"
echo "API Response Body: $API_BODY"
echo

if [ "$API_HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ API access to /me successful${NC}"
    echo "User Data from API (/me):"
    echo "$API_BODY" | jq .
else
    echo -e "${RED}✗ API access to /me failed (HTTP $API_HTTP_CODE)${NC}"
    
    # Additional debug: Try with verbose curl
    echo -e "\n${YELLOW}Debug: Running verbose curl request to /me endpoint...${NC}"
    curl -v -X GET http://localhost:8000/api/users/me \
      -H "Authorization: Bearer $USER_TOKEN" \
      -H "Content-Type: application/json"
    
    exit 1
fi

# Step 5: Decode and analyze the JWT token
echo -e "\n${YELLOW}5. Decoding and Analyzing JWT Token...${NC}"
if command -v jq &> /dev/null; then
    # Extract payload (second part of JWT)
    TOKEN_PAYLOAD=$(echo $USER_TOKEN | cut -d "." -f 2)
    # Add padding if necessary
    while [ $((${#TOKEN_PAYLOAD} % 4)) -ne 0 ]; do TOKEN_PAYLOAD+="="; done
    # Decode and print
    DECODED_PAYLOAD=$(echo $TOKEN_PAYLOAD | base64 -d 2>/dev/null | jq . 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Decoded Token Payload:${NC}"
        echo "$DECODED_PAYLOAD"
        
        # Check important claims
        echo -e "\n${YELLOW}Token Analysis:${NC}"
        ISS=$(echo "$DECODED_PAYLOAD" | jq -r '.iss')
        AUD=$(echo "$DECODED_PAYLOAD" | jq -r '.aud')
        EXP=$(echo "$DECODED_PAYLOAD" | jq -r '.exp')
        IAT=$(echo "$DECODED_PAYLOAD" | jq -r '.iat')
        SUB=$(echo "$DECODED_PAYLOAD" | jq -r '.sub')
        ROLES=$(echo "$DECODED_PAYLOAD" | jq -r '.realm_access.roles[]?' 2>/dev/null | tr '\n' ' ')
        
        echo "Issuer (iss): $ISS"
        echo "Audience (aud): $AUD"
        echo "Subject (sub): $SUB"
        echo "Expiration (exp): $EXP ($(date -d @$EXP 2>/dev/null || echo 'invalid date'))"
        echo "Issued At (iat): $IAT ($(date -d @$IAT 2>/dev/null || echo 'invalid date'))"
        echo "Roles: $ROLES"
        
        # Check if token is expired
        CURRENT_TIME=$(date +%s)
        if [ "$EXP" != "null" ] && [ $CURRENT_TIME -gt $EXP ]; then
            echo -e "${RED}✗ Token is EXPIRED!${NC}"
        else
            echo -e "${GREEN}✓ Token is not expired${NC}"
        fi
        
    else
        echo -e "${RED}✗ Failed to decode token payload${NC}"
        echo "Token payload part: $TOKEN_PAYLOAD"
    fi
else
    echo -e "${RED}✗ 'jq' not found. Cannot decode token.${NC}"
fi

# Step 6: Test with different endpoints for more info
echo -e "\n${YELLOW}6. Testing Other API Endpoints...${NC}"

echo "Testing /api/health (no auth required):"
curl -s -w "HTTP: %{http_code}\n" -X GET http://localhost:8000/api/health
echo

echo "Testing /api/users/me with verbose output:"
curl -v -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" 2>&1 | grep -E "(HTTP/|Authorization|Bearer|error|Invalid)"

echo -e "\n${GREEN}=== Test Complete ===${NC}"