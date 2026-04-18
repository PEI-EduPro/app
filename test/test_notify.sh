#!/bin/bash
# End-to-end test for notify-student endpoint
# Uses existing edupro realm users: manager / jra (professor)

set -e

KC_URL="http://localhost:8080"
API_BASE="http://localhost:8000/api"
REALM="edupro"
CLIENT_ID="frontend"  # public client, no secret needed

STUDENT_EMAIL="monteiro.fon@ua.pt"
STUDENT_EMAIL="trs.coelho@ua.pt"
STUDENT_NAME="TEMPLATE Student"
STUDENT_NMEC=12345

MANAGER_USER="manager"
MANAGER_PASS="admin"
REGENT_USER="jra"
REGENT_PASS="admin"
REGENT_ID="1be4fd85-f59c-4392-8830-d458f783bf1b"

DB_CONTAINER="edupro-db-1"
DB_USER="myuser"
DB_NAME="mydatabase"

# ─── TOKENS ──────────────────────────────────────────────────────────────────

get_token() {
  curl -s -X POST "$KC_URL/realms/$REALM/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$1&password=$2&grant_type=password&client_id=$CLIENT_ID" \
    | jq -r '.access_token'
}

echo "--- Getting tokens ---"
MANAGER_TOKEN=$(get_token "$MANAGER_USER" "$MANAGER_PASS")
REGENT_TOKEN=$(get_token "$REGENT_USER" "$REGENT_PASS")
[ "$MANAGER_TOKEN" = "null" ] && echo "Failed manager token" && exit 1
[ "$REGENT_TOKEN" = "null" ] && echo "Failed regent token" && exit 1
echo "Tokens OK"

# ─── SUBJECT ─────────────────────────────────────────────────────────────────

echo "--- Creating subject ---"
SUBJECT_RESP=$(curl -s -X POST "$API_BASE/subjects/" \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"TEMPLATE Subject\",\"regent_keycloak_id\":\"$REGENT_ID\"}")
SUBJECT_ID=$(echo "$SUBJECT_RESP" | jq -r '.id')
echo "Subject ID: $SUBJECT_ID"
[ "$SUBJECT_ID" = "null" ] && echo "Subject creation failed: $SUBJECT_RESP" && exit 1

# Refresh regent token (now has subject group)
REGENT_TOKEN=$(get_token "$REGENT_USER" "$REGENT_PASS")

# ─── TOPIC ───────────────────────────────────────────────────────────────────

echo "--- Creating topic ---"
TOPIC_RESP=$(curl -s -X POST "$API_BASE/topics/" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"TEMPLATE Topic\",\"subject_id\":$SUBJECT_ID}")
TOPIC_ID=$(echo "$TOPIC_RESP" | jq -r '.id')
echo "Topic ID: $TOPIC_ID"
[ "$TOPIC_ID" = "null" ] && echo "Topic creation failed: $TOPIC_RESP" && exit 1

# ─── QUESTIONS ───────────────────────────────────────────────────────────────

echo "--- Creating questions ---"
curl -s -X POST "$API_BASE/questions/" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q1\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":true},{\"option_text\":\"B\",\"value\":false},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]},
    {\"topic_id\":$TOPIC_ID,\"question_text\":\"TEMPLATE Q2\",\"question_options\":[
      {\"option_text\":\"A\",\"value\":false},{\"option_text\":\"B\",\"value\":true},
      {\"option_text\":\"C\",\"value\":false},{\"option_text\":\"D\",\"value\":false}]}
  ]" | jq -r '.[].id' | xargs -I{} echo "  Question ID: {}"

# ─── GENERATE EXAM ───────────────────────────────────────────────────────────

echo "--- Generating exam ---"
curl -s -X POST "$API_BASE/exams/generate" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"subject_id\": $SUBJECT_ID,
    \"fraction\": 25,
    \"exam_name\": \"TEMPLATE Exam\",
    \"topics\": [\"TEMPLATE Topic\"],
    \"number_questions\": {\"TEMPLATE Topic\": 20},
    \"relative_quotations\": {\"TEMPLATE Topic\": 1.0},
    \"num_variations\": 1,
    \"vigilant_keycloak_ids\": [],
    \"student_tuples\": [[$STUDENT_NMEC, \"$STUDENT_NAME\", \"$STUDENT_EMAIL\"]]
  }" -o /dev/null -w "HTTP %{http_code}\n"

# ─── GET IDs ─────────────────────────────────────────────────────────────────

echo "--- Fetching exam config and exam IDs ---"
REGENT_TOKEN=$(get_token "$REGENT_USER" "$REGENT_PASS")

EXAM_CONFIG_ID=$(curl -s "$API_BASE/exams/subject/$SUBJECT_ID/configs" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq -r '.[0].id')
echo "Exam Config ID: $EXAM_CONFIG_ID"

EXAM_ID=$(curl -s "$API_BASE/exams/$EXAM_CONFIG_ID/all_exams_info" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq -r '.[0].exam_id')
echo "Exam ID: $EXAM_ID"

WR_ID=$(curl -s "$API_BASE/waiting-rooms/professor/my-waiting-rooms" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq -r '.[] | select(.exam_name == "TEMPLATE Exam") | .waiting_room_id')
echo "Waiting Room ID: $WR_ID"

# ─── WAITING ROOM FLOW (writes nmec/name/email to exam) ──────────────────────

echo "--- Starting waiting room ---"
curl -s -X PATCH "$API_BASE/waiting-rooms/$WR_ID/start" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq -r '.state'

echo "--- Associating student to exam ---"
curl -s -X POST "$API_BASE/waiting-rooms/$WR_ID/student_to_exam" \
  -H "Authorization: Bearer $REGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"qr\":\"$EXAM_ID\",\"nmec\":$STUDENT_NMEC}" | jq -r '.message'

echo "--- Closing waiting room ---"
curl -s -X PATCH "$API_BASE/waiting-rooms/$WR_ID/close" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq -r '.state'

# ─── PATCH EXAM IN DB (bypass OMR) ───────────────────────────────────────────

echo "--- Patching exam grade/results/validated in DB ---"
RESULTS='{"0":{"A":true,"B":false,"C":false,"D":false},"1":{"A":false,"B":true,"C":false,"D":false},"2":{"A":false,"B":false,"C":true,"D":false},"3":{"A":false,"B":false,"C":false,"D":true},"4":{"A":true,"B":false,"C":false,"D":false},"5":{"A":false,"B":true,"C":false,"D":false},"6":{"A":false,"B":false,"C":true,"D":false},"7":{"A":false,"B":false,"C":false,"D":true},"8":{"A":true,"B":false,"C":false,"D":false},"9":{"A":false,"B":true,"C":false,"D":false},"10":{"A":false,"B":false,"C":true,"D":false},"11":{"A":false,"B":false,"C":false,"D":true},"12":{"A":true,"B":false,"C":false,"D":false},"13":{"A":false,"B":true,"C":false,"D":false},"14":{"A":false,"B":false,"C":true,"D":false},"15":{"A":false,"B":false,"C":false,"D":true},"16":{"A":true,"B":false,"C":false,"D":false},"17":{"A":false,"B":true,"C":false,"D":false},"18":{"A":false,"B":false,"C":true,"D":false},"19":{"A":false,"B":false,"C":false,"D":true}}'
RESULTS_DETAILS='{"0":{"correct":1,"incorrect":0,"erased":0},"1":{"correct":0,"incorrect":1,"erased":0},"2":{"correct":1,"incorrect":0,"erased":0},"3":{"correct":1,"incorrect":0,"erased":0},"4":{"correct":0,"incorrect":1,"erased":1},"5":{"correct":1,"incorrect":0,"erased":0},"6":{"correct":0,"incorrect":1,"erased":0},"7":{"correct":1,"incorrect":0,"erased":0},"8":{"correct":1,"incorrect":0,"erased":0},"9":{"correct":1,"incorrect":0,"erased":2},"10":{"correct":0,"incorrect":1,"erased":0},"11":{"correct":1,"incorrect":0,"erased":0},"12":{"correct":1,"incorrect":0,"erased":0},"13":{"correct":0,"incorrect":1,"erased":0},"14":{"correct":1,"incorrect":0,"erased":0},"15":{"correct":0,"incorrect":0,"erased":1},"16":{"correct":1,"incorrect":0,"erased":0},"17":{"correct":0,"incorrect":1,"erased":0},"18":{"correct":1,"incorrect":0,"erased":0},"19":{"correct":1,"incorrect":0,"erased":0}}'

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
  "UPDATE exam SET grade=15.5, results='$RESULTS', results_details='$RESULTS_DETAILS'::jsonb, capture_path='/tmp/fake.jpg', validated=true WHERE id=$EXAM_ID;"
echo "DB patched"

# ─── NOTIFY ──────────────────────────────────────────────────────────────────

echo "--- Calling notify-student ---"
REGENT_TOKEN=$(get_token "$REGENT_USER" "$REGENT_PASS")
curl -s -X POST "$API_BASE/exams/$EXAM_ID/notify-student" \
  -H "Authorization: Bearer $REGENT_TOKEN" | jq

# ─── CLEANUP ─────────────────────────────────────────────────────────────────

echo "--- Cleanup ---"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
  DELETE FROM warning;
  DELETE FROM waiting_room WHERE exam_config_id=$EXAM_CONFIG_ID;
  DELETE FROM exam WHERE exam_config_id=$EXAM_CONFIG_ID;
  DELETE FROM topic_config WHERE exam_config_id=$EXAM_CONFIG_ID;
  DELETE FROM exam_config WHERE id=$EXAM_CONFIG_ID;
  DELETE FROM question_option WHERE question_id IN (SELECT id FROM question WHERE topic_id=$TOPIC_ID);
  DELETE FROM question WHERE topic_id=$TOPIC_ID;
  DELETE FROM topic WHERE subject_id=$SUBJECT_ID;
  DELETE FROM subject WHERE id=$SUBJECT_ID;
" && echo "DB cleaned"

# Remove Keycloak groups created for the subject/waiting room
KC_ADMIN_TOKEN=$(curl -s -X POST "$KC_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin&grant_type=password&client_id=admin-cli" | jq -r '.access_token')
for GROUP_PATH in "/s$SUBJECT_ID" "/w$WR_ID"; do
  GROUP_ID=$(curl -s "$KC_URL/admin/realms/$REALM/groups?search=${GROUP_PATH##*/}" \
    -H "Authorization: Bearer $KC_ADMIN_TOKEN" | jq -r --arg p "$GROUP_PATH" '.[] | select(.path==$p) | .id')
  [ -n "$GROUP_ID" ] && [ "$GROUP_ID" != "null" ] && \
    curl -s -X DELETE "$KC_URL/admin/realms/$REALM/groups/$GROUP_ID" \
      -H "Authorization: Bearer $KC_ADMIN_TOKEN" && echo "Deleted KC group $GROUP_PATH"
done

echo "Done. Check $STUDENT_EMAIL for the notification email."
