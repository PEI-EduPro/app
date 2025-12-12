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
TIMESTAMP=$(date +%s)
SUBJECT_RESP=$(curl -s -X POST "$API_BASE/subjects/" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Exam Gen Test Subject $TIMESTAMP\"
  }")
SUBJECT_ID=$(echo $SUBJECT_RESP | jq -r '.id')
echo "Subject ID: $SUBJECT_ID"

# Function to create topic, questions and options
create_topic_content() {
    TOPIC_NAME=$1
    NUM_QUESTIONS=$2
    echo "Creating Topic '$TOPIC_NAME' with $NUM_QUESTIONS questions..."
    
    TOPIC_RESP=$(curl -s -X POST "$API_BASE/topics/" \
      -H "Authorization: Bearer $REGENT_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{ \"name\": \"$TOPIC_NAME\", \"subject_id\": $SUBJECT_ID }")
    TOPIC_ID=$(echo $TOPIC_RESP | jq -r '.id')
    
    case $TOPIC_NAME in
        "Calculus")
            QUESTIONS=(
                "What is the derivative of x squared?|2x|x|2|x squared"
                "What is the limit of (x squared - 1)/(x-1) as x approaches 1?|2|1|0|undefined"
                "What is d/dx(sin x)?|cos x|-cos x|sin x|-sin x"
                "What is d/dx(ln x)?|1/x|ln x|x|1"
                "What is the second derivative of x cubed?|6x|3x squared|x cubed|3x"
                "What is the derivative of tan x?|sec squared x|tan squared x|1|csc squared x"
                "What is d/dx(x to the 4th)?|4x cubed|x cubed|4x|x to the 4th"
                "What is the product rule?|(fg) prime = f prime g + fg prime|(fg) prime = f prime g prime|(fg) prime = f prime g - fg prime|(fg) prime = fg"
                "What is d/dx(cos x)?|-sin x|sin x|cos x|-cos x"
                "What is the derivative of sqrt(x)?|1/(2 sqrt x)|sqrt x|2 sqrt x|1/sqrt x"
                "What is d/dx(1/x)?|-1/x squared|1/x squared|-1/x|1/x"
                "What is the derivative of e to the x?|e to the x|x times e to the x-1|ln x|1/x"
                "What is the chain rule result?|f prime of g times g prime|f prime times g prime|f times g|f prime plus g prime"
                "What is the quotient rule numerator?|f prime g minus fg prime|f prime g prime|f prime g plus fg prime|fg prime"
                "What is the derivative of x cubed?|3x squared|x squared|3x|x cubed"
                "What is d/dx(2x)?|2|2x|x|0"
                "What is the derivative of a constant?|0|1|constant|undefined"
                "What is d/dx(x)?|1|x|0|undefined"
                "What is the power rule for x to the n?|n times x to the n-1|x to the n|n times x|x to the n+1"
                "What is d/dx(5x squared)?|10x|5x|10|5x squared"
            )
            ;;
        "Algebra")
            QUESTIONS=(
                "Solve: 2x + 5 = 13|x = 4|x = 8|x = 9|x = 3"
                "Simplify: (x squared) cubed|x to the 6th|x to the 5th|x to the 9th|x to the 8th"
                "Factor: x squared - 9|(x-3)(x+3)|(x-9)(x+1)|x(x-9)|(x-3) squared"
                "Solve: x squared - 5x + 6 = 0|x = 2, 3|x = 1, 6|x = -2, -3|x = 0, 5"
                "Simplify: 3x + 2x|5x|6x|5x squared|6"
                "What is the slope of y = 3x + 2?|3|2|5|1"
                "Solve: 3(x-2) = 9|x = 5|x = 3|x = 7|x = 11"
                "Expand: (x+2) squared|x squared + 4x + 4|x squared + 4|x squared + 2x + 4|x squared + 4x + 2"
                "Simplify: x to the 5th / x squared|x cubed|x to the 7th|x to the 10th|x to the 2.5"
                "Solve: absolute value of x = 5|x = plus or minus 5|x = 5|x = -5|x = 25"
                "What is the y-intercept of y = 2x - 7?|-7|2|7|-2"
                "Factor: 2x squared + 8x|2x(x+4)|2(x squared + 4x)|x(2x+8)|2x squared (1+4x)"
                "Solve: x/3 = 4|x = 12|x = 7|x = 1|x = 4"
                "Simplify: (2x) cubed|8x cubed|6x cubed|2x cubed|8x"
                "What is sqrt(x squared)?|absolute x|x|-x|x squared"
                "Solve: 5x - 3 = 2x + 9|x = 4|x = 6|x = 2|x = 12"
                "Expand: (x-3)(x+3)|x squared - 9|x squared + 9|x squared - 6x + 9|x squared + 6x - 9"
                "Simplify: 3x squared times 2x|6x cubed|5x cubed|6x squared|5x squared"
                "Solve: x squared = 16|x = plus or minus 4|x = 4|x = 8|x = 256"
                "What is (x cubed) to the 0?|1|0|x cubed|x"
            )
            ;;
        "Geometry")
            QUESTIONS=(
                "Area of a circle with radius 5?|25 pi|10 pi|5 pi|50 pi"
                "Sum of angles in a triangle?|180 degrees|360 degrees|90 degrees|270 degrees"
                "Pythagorean theorem: a squared + b squared = ?|c squared|ab|2c|a+b"
                "Volume of a cube with side 3?|27|9|18|81"
                "Perimeter of a square with side 4?|16|8|12|20"
                "Area of a rectangle 5 by 3?|15|8|30|18"
                "Circumference of circle radius 2?|4 pi|2 pi|8 pi|pi"
                "How many sides in a hexagon?|6|5|7|8"
                "Area of triangle base 6, height 4?|12|24|10|20"
                "Diagonal of square side 1?|sqrt 2|1|2|sqrt 3"
                "Volume of sphere radius 3?|36 pi|27 pi|9 pi|12 pi"
                "Sum of angles in a quadrilateral?|360 degrees|180 degrees|270 degrees|540 degrees"
                "Area of trapezoid (b1=4,b2=6,h=5)?|25|50|20|30"
                "Surface area of cube side 2?|24|8|12|16"
                "Complementary angle to 30 degrees?|60 degrees|150 degrees|90 degrees|120 degrees"
            )
            ;;
        "Statistics")
            QUESTIONS=(
                "Mean of {2,4,6,8,10}?|6|5|7|8"
                "Median of {1,3,5,7,9}?|5|3|6|7"
                "Mode of {2,3,3,4,5}?|3|2|4|5"
                "Range of {10,20,30,40}?|30|40|20|50"
                "What is the sample space of a coin flip?|{H,T}|{1,2}|{H,T,E}|{0,1}"
                "Probability of rolling a 3 on a die?|1/6|1/3|1/2|1/12"
                "Mean of {5,5,5,5}?|5|20|0|10"
                "Median of {2,4,6,8}?|5|4|6|7"
                "Standard deviation measures what?|Spread|Center|Mode|Range"
                "What is P(A union B) if A,B disjoint?|P(A)+P(B)|P(A) times P(B)|P(A)-P(B)|1"
                "Variance is the square of what?|Standard deviation|Mean|Median|Range"
                "What percentile is the median?|50th|25th|75th|100th"
                "In a normal distribution, mean equals?|Median|Mode|Both|Neither"
                "Probability of certain event?|1|0|0.5|infinity"
                "What is the complement of P(A)?|1-P(A)|P(A)|1+P(A)|1/P(A)"
            )
            ;;
        "Trigonometry")
            QUESTIONS=(
                "What is sin(90 degrees)?|1|0|-1|sqrt2/2"
                "What is cos(0 degrees)?|1|0|-1|sqrt3/2"
                "What is tan(45 degrees)?|1|0|sqrt3|1/2"
                "sin squared theta + cos squared theta = ?|1|0|2|theta"
                "What is sin(30 degrees)?|1/2|sqrt3/2|1|0"
                "What is cos(60 degrees)?|1/2|sqrt3/2|1|0"
                "What is tan(0 degrees)?|0|1|infinity|undefined"
                "Period of sin(x)?|2 pi|pi|pi/2|4 pi"
                "What is sin(180 degrees)?|0|1|-1|sqrt2"
                "What is cos(90 degrees)?|0|1|-1|1/2"
            )
            ;;
    esac
    
    for i in $(seq 1 $NUM_QUESTIONS); do
        if [ $i -le ${#QUESTIONS[@]} ]; then
            IFS='|' read -r Q_TEXT OPT_A OPT_B OPT_C OPT_D <<< "${QUESTIONS[$((i-1))]}"
            
            Q_RESP=$(curl -s -X POST "$API_BASE/questions/" \
              -H "Authorization: Bearer $REGENT_TOKEN" \
              -H "Content-Type: application/json" \
              -d "[{ \"topic_id\": $TOPIC_ID, \"question_text\": \"$Q_TEXT\" }]")
            Q_ID=$(echo $Q_RESP | jq -r 'if type=="array" then .[0].id else .id end')
            
            curl -s -X POST "$API_BASE/question-options/" \
              -H "Authorization: Bearer $REGENT_TOKEN" \
              -H "Content-Type: application/json" \
              -d "{ \"question_id\": $Q_ID, \"option_text\": \"$OPT_A\", \"value\": true }" > /dev/null
            
            curl -s -X POST "$API_BASE/question-options/" \
              -H "Authorization: Bearer $REGENT_TOKEN" \
              -H "Content-Type: application/json" \
              -d "{ \"question_id\": $Q_ID, \"option_text\": \"$OPT_B\", \"value\": false }" > /dev/null
            
            curl -s -X POST "$API_BASE/question-options/" \
              -H "Authorization: Bearer $REGENT_TOKEN" \
              -H "Content-Type: application/json" \
              -d "{ \"question_id\": $Q_ID, \"option_text\": \"$OPT_C\", \"value\": false }" > /dev/null
            
            curl -s -X POST "$API_BASE/question-options/" \
              -H "Authorization: Bearer $REGENT_TOKEN" \
              -H "Content-Type: application/json" \
              -d "{ \"question_id\": $Q_ID, \"option_text\": \"$OPT_D\", \"value\": false }" > /dev/null
        fi
    done
}

create_topic_content "Calculus" 20
create_topic_content "Algebra" 20
create_topic_content "Geometry" 15
create_topic_content "Statistics" 15
create_topic_content "Trigonometry" 10

echo "All topics and questions created."


echo -e "\n--- 3. TEST EXAM GENERATION ---"

echo "Generating 3 exam variations (requesting ZIP)..."

HTTP_CODE=$(curl -w "%{http_code}" -X POST "$API_BASE/exams/generate" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"subject_id\": $SUBJECT_ID,
    \"fraction\": 25,
    \"num_variations\": 3,
    \"topics\": [\"Calculus\", \"Algebra\", \"Geometry\", \"Statistics\", \"Trigonometry\"],
    \"number_questions\": { 
        \"Calculus\": 5,
        \"Algebra\": 5,
        \"Geometry\": 3,
        \"Statistics\": 4,
        \"Trigonometry\": 3
    },
    \"relative_quotations\": { 
        \"Calculus\": 2.0,
        \"Algebra\": 2.0,
        \"Geometry\": 1.5,
        \"Statistics\": 1.5,
        \"Trigonometry\": 1.0
    }
  }" \
  -o generated_exams.zip)

if [ "$HTTP_CODE" -eq 200 ] && [ -f "generated_exams.zip" ]; then
    echo "SUCCESS: 'generated_exams.zip' file received (HTTP $HTTP_CODE)."
    echo "File size: $(du -h generated_exams.zip | cut -f1)"
    
    if unzip -t generated_exams.zip > /dev/null 2>&1; then
        echo "ZIP integrity check passed."
        echo "Contents:"
        unzip -l generated_exams.zip
    else
        echo "ERROR: Received file is not a valid ZIP. File content:"
        cat generated_exams.zip
    fi
else
    echo "ERROR: Request failed (HTTP $HTTP_CODE). Response:"
    cat generated_exams.zip 2>/dev/null || echo "No response file created"
fi

echo -e "\n--- 3.1 GET EXAM CONFIGS ---"
echo "Fetching exam configs for subject $SUBJECT_ID..."
curl -s -X GET "$API_BASE/exams/subject/$SUBJECT_ID/configs" | jq .

echo -e "\n--- 4. CLEANUP ---"
curl -s -X DELETE "$API_BASE/subjects/$SUBJECT_ID" \
  -H "Authorization: Bearer $MANAGER_TOKEN"
echo "Subject deleted."
# rm generated_exams.zip
echo "Cleanup done. File 'generated_exams.zip' saved in current directory."
