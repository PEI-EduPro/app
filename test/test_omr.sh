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
PASSWORD="admin"

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
echo "--- Sending image to OMR evaluation endpoint ---"
curl -v -X POST "$API_BASE/exams/evaluate" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$IMAGE_PATH"
