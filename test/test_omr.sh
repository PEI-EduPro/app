#!/bin/bash

# --- CONFIGURATION ---
KC_URL="http://localhost:8080"
API_BASE="http://localhost:8000/api"
#REALM="master"
REALM="edupro"
# CLIENT_ID="api-backend"
CLIENT_ID="frontend"
CLIENT_SECRET="**"  # <--- paste KEYCLOAK_CLIENT_SECRET from deployment/.env

# USERNAME="professor1"
USERNAME="orp"
# PASSWORD="password"
PASSWORD="adminadminadmin1"

IMAGE_PATH="${1:-}"  # Pass image path as first argument

# --- VALIDATE ---
if [ -z "$IMAGE_PATH" ]; then
    echo "Usage: $0 <path_to_exam_image>"
    exit 1
fi

if [ ! -f "$IMAGE_PATH" ]; then
    echo "Error: File '$IMAGE_PATH' not found."
    exit 1
fi

# --- GET TOKEN ---
echo "--- Getting Keycloak token for '$USERNAME' ---"
TOKEN=$(curl -s -X POST "$KC_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME" \
  -d "password=$PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "Failed to get token. Check credentials and Keycloak config."
    exit 1
fi
echo "Token obtained."

# --- CALL OMR ENDPOINT ---
echo ""
echo "--- Building JSON payload file ---"
# Create a secure temporary file
TEMP_JSON=$(mktemp)

# 1. Write the opening JSON brackets
echo -n '{"files": ["' > "$TEMP_JSON"

# 2. Convert to Base64 and append DIRECTLY to the file 
# (This completely bypasses the shell's argument limits!)
base64 -w 0 "$IMAGE_PATH" >> "$TEMP_JSON"

# 3. Write the closing JSON brackets
echo '"]}' >> "$TEMP_JSON"

echo "--- Sending JSON payload to OMR evaluation endpoint ---"
curl -v -X POST "$API_BASE/waiting-rooms/1/evaluate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @"$TEMP_JSON"

# Clean up the temporary file
rm "$TEMP_JSON"