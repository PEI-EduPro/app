#!/bin/bash

# --- CONFIGURATION ---
KC_URL="http://localhost:8080"
API_URL="http://localhost:8000/api/subjects"
REALM="master"
CLIENT_ID="api-backend"
CLIENT_SECRET="**********" # <--- PASTE SECRET HERE
API_BASE="http://localhost:8000/api"

echo "--- 1. SETTING UP KEYCLOAK ADMIN ---"
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
      }"
    
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
      -d "[{ \"id\": \"$ROLE_ID\", \"name\": \"$ROLE_NAME\" }]"
    
    echo "Role '$ROLE_NAME' assigned to user $USER_ID"
}

echo "--- 2. CREATING USERS ---"
echo "Creating Manager..."
MANAGER_ID=$(create_user "manager_user" "123" "Manager" "Boss")
echo "Manager ID: $MANAGER_ID"

echo "Creating Regent..."
REGENT_ID=$(create_user "regent_user" "123" "Regent" "Teacher")
echo "Regent ID: $REGENT_ID"

echo "Creating Professor..."
PROF_ID=$(create_user "prof_user" "123" "Professor" "Helper")
echo "Professor ID: $PROF_ID"

echo "Creating Student..."
STUDENT_ID=$(create_user "student_user" "123" "Student" "Learner")
echo "Student ID: $STUDENT_ID"

echo "--- 3. ASSIGNING ROLES ---"
assign_role $MANAGER_ID "manager"
# Assign professor role to Regent and Professor
assign_role $REGENT_ID "professor" 
assign_role $PROF_ID "professor"
# Assign student role to Student
assign_role $STUDENT_ID "student"


echo "--- 4. GETTING TOKENS ---"
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
STUDENT_TOKEN=$(get_token "student_user" "123")

echo "Tokens acquired."

# ==============================================================================
# API TESTS START HERE
# ==============================================================================

echo -e "\n\n=== TEST 1: POST /subject (Create Subject) ==="
# Manager creates a subject and assigns regent_user
RESPONSE=$(curl -s -X POST "$API_URL/" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Math 101\",
    \"regent_keycloak_id\": \"$REGENT_ID\"
  }")

echo "Response: $RESPONSE"
SUBJECT_ID=$(echo $RESPONSE | jq -r '.id')
echo "Created Subject ID: $SUBJECT_ID"

echo -e "\n=== TEST 2: PUT /subject/{id} (Update Subject Name) ==="
# Manager renames the subject
curl -s -X PUT "$API_URL/$SUBJECT_ID" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Advanced Mathematics 101"
  }' | jq

echo -e "\n=== TEST 3: POST /subject/{id}/professors (Add Professor) ==="
# Manager adds 'prof_user' with specific permissions
curl -s -X POST "$API_URL/$SUBJECT_ID/professors" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"professor_keycloak_id\": \"$PROF_ID\",
    \"edit_topics\": false,
    \"edit_questions\": true,
    \"view_question_bank\": true,
    \"add_students\": false,
    \"generate_exams\": false,
    \"view_grades\": false,
    \"auto_correct_exams\": false
  }" | jq

echo -e "\n=== TEST 4: PUT /subject/{id}/professors/{pid} (Update Permissions) ==="
# Manager grants 'add_students' permission to the professor
curl -s -X PUT "$API_URL/$SUBJECT_ID/professors/$PROF_ID" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "edit_questions": true,
    "add_students": true
  }' | jq

echo -e "\n=== TEST 5: POST /subject/{id}/students (Add Student) ==="
# Manager adds 'student_user' to the subject
curl -s -X POST "$API_URL/$SUBJECT_ID/students" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"student_keycloak_ids\": [\"$STUDENT_ID\"]
  }" | jq

echo -e "\n=== TEST 6: GET /subject/{id}/students (View Students) ==="
# Regent (not manager) tries to view students. Should succeed.
echo "Requesting as Regent User..."
REGENT_TOKEN=$(get_token "regent_user" "123")
curl -s -X GET "$API_URL/$SUBJECT_ID/students" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq

echo -e "\n=== TEST 7: GET /subject (List access check) ==="
echo "Manager View (Should see subject):"
curl -s -X GET "$API_URL/" \
  -H "Authorization: Bearer $MANAGER_TOKEN" | jq

echo "Student View (Should see subject because they were added):"
# Note: We need to refresh the Student Token to see the new group claim!
STUDENT_TOKEN_REFRESHED=$(get_token "student_user" "123")

curl -s -X GET "$API_URL/" \
  -H "Authorization: Bearer $STUDENT_TOKEN_REFRESHED" | jq

echo -e "\n=== TEST 8: DELETE /subject/{id}/professors/{pid} (Remove Professor) ==="
curl -s -X DELETE "$API_URL/$SUBJECT_ID/professors/$PROF_ID" \
  -H "Authorization: Bearer $MANAGER_TOKEN" 

echo "Professor removed (No Content)."

echo -e "\n=== TEST 9: DELETE /subject/{id} (Delete Subject) ==="
# Delete the subject and cleanup Keycloak groups
curl -s -X DELETE "$API_URL/$SUBJECT_ID" \
  -H "Authorization: Bearer $MANAGER_TOKEN"

echo "Subject Deleted (No Content)."

echo -e "\n=== TEST 10: Verify Deletion ==="
curl -s -X GET "$API_URL/" \
  -H "Authorization: Bearer $MANAGER_TOKEN" | jq


# For safety, let's create a new subject specifically for the new tests to ensure clean state.

echo -e "\n\n=== SETUP FOR NEW FEATURES ==="
echo "Creating a dedicated subject for Topics/Questions..."
SUBJECT_RESPONSE=$(curl -s -X POST "$API_BASE/subjects/" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Análise Real\",
    \"regent_keycloak_id\": \"$REGENT_ID\"
  }")
NEW_SUBJECT_ID=$(echo $SUBJECT_RESPONSE | jq -r '.id')
echo "New Subject ID: $NEW_SUBJECT_ID"

# ==============================================================================
# NEW FEATURE TESTS (Topics -> Questions -> Options)
# ==============================================================================

echo -e "\n=== TEST 11.1: POST /api/topics (Create Topic) ==="
# Based on PR: {"name": "Diferenciação em R", "subject_id": 1}
TOPIC_RESPONSE=$(curl -s -X POST "$API_BASE/topics/" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Diferenciação em R\", 
    \"subject_id\": $NEW_SUBJECT_ID
  }")

echo "Response: $TOPIC_RESPONSE"
TOPIC_ID=$(echo $TOPIC_RESPONSE | jq -r '.id')
echo "Created Topic ID: $TOPIC_ID"

echo -e "\n=== TEST 11.2: POST /api/topics (Create Topic) ==="
# Based on PR: {"name": "Diferenciação em R", "subject_id": 1}
TOPIC_RESPONSE=$(curl -s -X POST "$API_BASE/topics/" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Integracao\", 
    \"subject_id\": $NEW_SUBJECT_ID
  }")

echo "Response: $TOPIC_RESPONSE"
TOPIC_ID=$(echo $TOPIC_RESPONSE | jq -r '.id')
echo "Created Topic ID: $TOPIC_ID"

echo -e "\n=== TEST 11.3: POST /api/topics (Create Topic) ==="
# Based on PR: {"name": "Diferenciação em R", "subject_id": 1}
TOPIC_RESPONSE=$(curl -s -X POST "$API_BASE/topics/" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Transformadas de Laplace\", 
    \"subject_id\": $NEW_SUBJECT_ID
  }")

echo "Response: $TOPIC_RESPONSE"
TOPIC_ID=$(echo $TOPIC_RESPONSE | jq -r '.id')
echo "Created Topic ID: $TOPIC_ID"

echo -e "\n=== TEST 11.4: POST /api/exams/generate (Create Exam Config) ==="
# Create exam configuration with the three topics created above
EXAM_RESPONSE=$(curl -s -X POST "$API_BASE/exams/generate" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"subject_id\": $NEW_SUBJECT_ID,
    \"fraction\": -20,
    \"topics\": [\"Diferenciação em R\", \"Integracao\", \"Transformadas de Laplace\"],
    \"number_questions\": {
      \"Diferenciação em R\": 1,
      \"Integracao\": 2,
      \"Transformadas de Laplace\": 3
    },
    \"relative_quotations\": {
      \"Diferenciação em R\": 1,
      \"Integracao\": 2,
      \"Transformadas de Laplace\": 2
    }
  }")

echo "Response: $EXAM_RESPONSE"
EXAM_CONFIG_ID=$(echo $EXAM_RESPONSE | jq -r '.id // .exam_config_id // .')
echo "Created Exam Config ID: $EXAM_CONFIG_ID"


echo -e "\n=== TEST 12: GET /api/topics/{id} (Read Topic) ==="
# Note: The PR implemented getting by NAME, not ID.
curl -s -X GET "$API_BASE/topics/$TOPIC_ID" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq

echo -e "\n=== TEST 13: POST /api/questions (Create Multiple Questions) ==="
# Create multiple questions at once
QUESTION_RESPONSE=$(curl -s -X POST "$API_BASE/questions/" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[
    {
      \"topic_id\": $TOPIC_ID,
      \"question_text\": \"Uma função é diferenciável se: \"
    },
    {
      \"topic_id\": $TOPIC_ID,
      \"question_text\": \"O limite de uma função existe quando: \"
    },
    {
      \"topic_id\": $TOPIC_ID,
      \"question_text\": \"Uma função contínua é aquela que: \"
    }
  ]")

echo "Response: $QUESTION_RESPONSE"
# Extract the first question ID for later tests
QUESTION_ID=$(echo $QUESTION_RESPONSE | jq -r '.[0].id')
echo "Created Questions. First Question ID: $QUESTION_ID"
echo "All Question IDs: $(echo $QUESTION_RESPONSE | jq -r '.[].id')"

echo -e "\n=== TEST 14: POST /api/question-options (Create Option) ==="
# Based on PR: {"question_id": 1, "option_text": "For contínua.", "value": false}
OPTION_RESPONSE=$(curl -s -X POST "$API_BASE/question-options/" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"question_id\": $QUESTION_ID,
    \"option_text\": \"For contínua.\",
    \"value\": false
  }")

echo "Response: $OPTION_RESPONSE"

echo -e "\n=== TEST 15: GET /api/questions/{id}/question-options (Professor Gets Options) ==="
# Professor gets all options for a question
PROF_TOKEN=$(get_token "prof_user" "123")
RESPONSE=$(curl -s -X GET "$API_BASE/questions/$QUESTION_ID/question-options" \
  -H "Authorization: Bearer $PROF_TOKEN")
echo "Raw Response: $RESPONSE"
echo "$RESPONSE" | jq 2>/dev/null || echo "Failed to parse JSON"


echo -e "\n=== TEST 16: GET /api/questions/{id} (Verify Question & Options) ==="
# Assuming GET question returns the question details
curl -s -X GET "$API_BASE/questions/$QUESTION_ID" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq

# ==============================================================================
# CLEANUP
# ==============================================================================
echo -e "\n=== CLEANUP: Delete Subject (Cascades to Topics/Questions) ==="
curl -s -X DELETE "$API_BASE/subjects/$NEW_SUBJECT_ID" \
  -H "Authorization: Bearer $MANAGER_TOKEN"

echo "Cleanup complete."


echo -e "\n\nDONE."