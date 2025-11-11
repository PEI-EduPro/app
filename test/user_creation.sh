#!/bin/bash

echo "=== Complete User Creation & Authentication Test ==="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

CLIENT_SECRET="RdwcPv5Gp0Nq3Pm8fGV4HfpST4KurVhb"

# Step 1: Get Admin Token
echo -e "\n${YELLOW}1. Getting Admin Token...${NC}"
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" != "null" ]; then
    echo -e "${GREEN}✓ Admin token obtained${NC}"
else
    echo -e "${RED}✗ Failed to get admin token${NC}"
    exit 1
fi

# Step 2: Create New User
echo -e "\n${YELLOW}2. Creating New User...${NC}"
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

if [ "$HTTP_CODE" = "201" ]; then
    echo -e "${GREEN}✓ User created successfully${NC}"
    
    # Get the user ID from Location header (if available)
    LOCATION_HEADER=$(echo "$USER_RESPONSE" | grep -i "Location:" | head -n1)
    echo "User created: $LOCATION_HEADER"
else
    echo -e "${RED}✗ User creation failed (HTTP $HTTP_CODE)${NC}"
    echo "Response: $(echo "$USER_RESPONSE" | head -n1)"
fi

# Step 3: Get Token as New User
echo -e "\n${YELLOW}3. Getting Token as New User...${NC}"
USER_TOKEN=$(curl -s -X POST http://localhost:8080/realms/EduPro/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=newstudent" \
  -d "password=newpassword123" \
  -d "grant_type=password" \
  -d "client_id=api-backend" \
  -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token')

if [ "$USER_TOKEN" != "null" ]; then
    echo -e "${GREEN}✓ User token obtained successfully${NC}"
    echo "Token: ${USER_TOKEN:0:50}..."
else
    echo -e "${RED}✗ Failed to get user token${NC}"
    exit 1
fi

# Step 4: Test API Access
echo -e "\n${YELLOW}4. Testing API Access...${NC}"
API_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $USER_TOKEN")

API_HTTP_CODE=$(echo "$API_RESPONSE" | tail -n1)
API_BODY=$(echo "$API_RESPONSE" | head -n1)

if [ "$API_HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ API access successful${NC}"
    echo "User Data:"
    echo "$API_BODY" | jq .
else
    echo -e "${RED}✗ API access failed (HTTP $API_HTTP_CODE)${NC}"
    echo "Error: $API_BODY"
fi

# Step 5: Verify Database
echo -e "\n${YELLOW}5. Checking Database...${NC}"
DB_RESULT=$(docker compose exec db psql -U myuser -d mydatabase -t -c "SELECT id, email, name, role FROM \"user\" WHERE email = 'newstudent@example.com';" 2>/dev/null)

if [ -n "$DB_RESULT" ]; then
    echo -e "${GREEN}✓ User found in database${NC}"
    echo "Database Record: $DB_RESULT"
else
    echo -e "${RED}✗ User not found in database${NC}"
fi

echo -e "\n${GREEN}=== Test Complete ===${NC}"