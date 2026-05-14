#!/bin/bash

# --- CONFIGURATION ---
KC_URL="http://localhost:8080"
API_BASE="http://localhost:8000/api"
REALM="edupro"
CLIENT_ID="frontend"
CLIENT_SECRET="**"  # <--- paste KEYCLOAK_CLIENT_SECRET from deployment/.env

USERNAME="orp"
PASSWORD="adminadminadmin1"

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

# --- CALL NOTIFY ENDPOINT ---
WAITING_ROOM_ID=1

echo ""
echo "--- Triggering email notifications for waiting room $WAITING_ROOM_ID ---"

# 1. Define your JSON payload using a heredoc
JSON_PAYLOAD=$(cat <<EOF
{
  "exam_capture": true,
  "student_identification": true,
  "question_weights": true,
  "red_green_cross_table": true,
  "cumulative_score_table": true
}
EOF
)

# 2. Add the Content-Type header and pass the payload using -d
curl -v -X POST "$API_BASE/waiting-rooms/$WAITING_ROOM_ID/notify-students" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD"

echo ""
echo "--- Request complete ---"