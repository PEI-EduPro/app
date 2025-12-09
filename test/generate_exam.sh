#!/bin/bash

# --- CONFIGURATION ---
KC_URL="http://localhost:8080"
API_BASE="http://localhost:8000/api"
REALM="master"
CLIENT_ID="api-backend"
CLIENT_SECRET="**********" # <--- PASTE SECRET HERE

echo "--- 1. AUTHENTICATION & USER SETUP ---"

# 1.1 Get Admin Token
ADMIN_TOKEN=$(curl -s -X POST $KC_URL/realms/$REALM/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ]; then echo "Failed to get Admin Token"; exit 1; fi

# Function to create a user and return their ID
create_user() {
    USERNAME=$1
    PASSWORD=$2
    FIRST=$3
    LAST=$4
    
    # Create User
    curl -s -X POST $KC_URL/admin/realms/$REALM/users \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"username\": \"$USERNAME\",
        \"email\": \"$USERNAME@example.com\",
        \"firstName\": \"$FIRST\",
        \"lastName\": \"$LAST\",
        \"enabled\": true,
        \"emailVerified\": true,
        \"credentials\": [{ \"type\": \"password\", \"value\": \"$PASSWORD\", \"temporary\": false }]
      }" > /dev/null
    
    # Get ID
    USER_ID=$(curl -s -X GET "$KC_URL/admin/realms/$REALM/users?username=$USERNAME" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')
    echo $USER_ID
}

# Function to assign a realm role to a user
assign_role() {
    USER_ID=$1
    ROLE_NAME=$2
    
    # Get Role ID
    ROLE_ID=$(curl -s -X GET "$KC_URL/admin/realms/$REALM/roles/$ROLE_NAME" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')
    
    if [ "$ROLE_ID" == "null" ]; then
        echo "Warning: Role '$ROLE_NAME' does not exist in Keycloak. Skipping assignment."
        return
    fi

    # Assign Role
    curl -s -X POST "$KC_URL/admin/realms/$REALM/users/$USER_ID/role-mappings/realm" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "[{ \"id\": \"$ROLE_ID\", \"name\": \"$ROLE_NAME\" }]" > /dev/null
    
    echo "Role '$ROLE_NAME' assigned to user $USER_ID"
}

# 1.2 Create Users
echo "Creating Manager..."
MANAGER_ID=$(create_user "manager_user" "123" "Manager" "Boss")
echo "Manager ID: $MANAGER_ID"

echo "Creating Regent..."
REGENT_ID=$(create_user "regent_user" "123" "Regent" "Teacher")
echo "Regent ID: $REGENT_ID"

# 1.3 Assign Roles
assign_role $MANAGER_ID "manager"
assign_role $REGENT_ID "professor"

# 1.4 Get Tokens for API Access
get_token() {
    curl -s -X POST $KC_URL/realms/$REALM/protocol/openid-connect/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$1" \
    -d "password=$2" \
    -d "grant_type=password" \
    -d "client_id=$CLIENT_ID" \
    -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token'
}

MANAGER_TOKEN=$(get_token "manager_user" "123")
REGENT_TOKEN=$(get_token "regent_user" "123")

if [ "$MANAGER_TOKEN" == "null" ] || [ "$REGENT_TOKEN" == "null" ]; then
    echo "Error: Failed to get tokens."
    exit 1
fi

echo "Tokens acquired."

echo -e "\n--- 2. SETUP DATA (Subject -> Topics -> Questions) ---"

# Create Subject
echo "Creating Subject..."
SUBJECT_RESP=$(curl -s -X POST "$API_BASE/subjects/" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Exam Gen Test Subject\",
    \"regent_keycloak_id\": \"$REGENT_ID\"
  }")
SUBJECT_ID=$(echo $SUBJECT_RESP | jq -r '.id')
echo "Subject ID: $SUBJECT_ID"

# Function to create topic, questions and options
create_topic_content() {
    TOPIC_NAME=$1
    echo "Creating Topic '$TOPIC_NAME' with questions..."
    
    # Create Topic
    TOPIC_RESP=$(curl -s -X POST "$API_BASE/topics/" \
      -H "Authorization: Bearer $REGENT_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{ \"name\": \"$TOPIC_NAME\", \"subject_id\": $SUBJECT_ID }")
    TOPIC_ID=$(echo $TOPIC_RESP | jq -r '.id')
    
    # Create 10 Questions
    for i in {1..10}; do
        Q_RESP=$(curl -s -X POST "$API_BASE/questions/" \
          -H "Authorization: Bearer $REGENT_TOKEN" \
          -H "Content-Type: application/json" \
          -d "[{ \"topic_id\": $TOPIC_ID, \"question_text\": \"$TOPIC_NAME Q$i: Solve for x...\" }]")
        Q_ID=$(echo $Q_RESP | jq -r '.[0].id')
        
        # Create 4 Options
        # Option A (Correct)
        curl -s -X POST "$API_BASE/question-options/" \
          -H "Authorization: Bearer $REGENT_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{ \"question_id\": $Q_ID, \"option_text\": \"Answer A (Correct) - $TOPIC_NAME Q$i\", \"value\": true }"
        
        # Option B (Wrong)
        curl -s -X POST "$API_BASE/question-options/" \
          -H "Authorization: Bearer $REGENT_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{ \"question_id\": $Q_ID, \"option_text\": \"Answer B (Wrong) - $TOPIC_NAME Q$i\", \"value\": false }"
          
        # Option C (Wrong)
        curl -s -X POST "$API_BASE/question-options/" \
          -H "Authorization: Bearer $REGENT_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{ \"question_id\": $Q_ID, \"option_text\": \"Answer C (Wrong) - $TOPIC_NAME Q$i\", \"value\": false }"

        # Option D (Wrong)
        curl -s -X POST "$API_BASE/question-options/" \
          -H "Authorization: Bearer $REGENT_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{ \"question_id\": $Q_ID, \"option_text\": \"Answer D (Wrong) - $TOPIC_NAME Q$i\", \"value\": false }"
    done
}

create_topic_content "Calculus"
create_topic_content "Algebra"

echo "Questions created."


echo -e "\n--- 3. TEST EXAM GENERATION ---"

# Generate 3 variations
# Calculus: 2 questions (Weight 1.0) -> Mass 2
# Algebra: 3 questions (Weight 2.0) -> Mass 6
# Total Mass: 8
# Normalization: 20/8 = 2.5
# Exp Weights: Calc=2.5, Alg=5.0
echo "Generating 3 exam variations (requesting ZIP)..."

curl -X POST "$API_BASE/exams/generate" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"subject_id\": $SUBJECT_ID,
    \"fraction\": 25,
    \"num_variations\": 3,
    \"topics\": [\"Calculus\", \"Algebra\"],
    \"number_questions\": { 
        \"Calculus\": 2,
        \"Algebra\": 3
    },
    \"relative_quotations\": { 
        \"Calculus\": 1.0,
        \"Algebra\": 2.0
    }
  }" \
  --output generated_exams.zip

if [ -f "generated_exams.zip" ]; then
    echo "SUCCESS: 'generated_exams.zip' file received."
    echo "File size: $(du -h generated_exams.zip | cut -f1)"
    
    # Check if it's a valid zip
    if unzip -t generated_exams.zip > /dev/null; then
        echo "ZIP integrity check passed."
        echo "Contents:"
        unzip -l generated_exams.zip
    else
        echo "ERROR: Received file is not a valid ZIP. File content:"
        cat generated_exams.zip
        echo ""
    fi
else
    echo "ERROR: Failed to download ZIP file."
    cat generated_exams.zip # Print content (might be error JSON)
fi


echo -e "\n--- 4. CLEANUP ---"
curl -s -X DELETE "$API_BASE/subjects/$SUBJECT_ID" \
  -H "Authorization: Bearer $MANAGER_TOKEN"
echo "Subject deleted."
# rm generated_exams.zip
echo "Cleanup done. File 'generated_exams.zip' saved in current directory."
