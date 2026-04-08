# TODO - fix/missing-parametrization

## Missing `response_model` on endpoints that return data

### exam.py

- [ ] `POST /generate` — returns ZIP, SKIP
- [x] `POST /exam/{exam_config_id}/student_list` — returns `{"message": ...}`
- [x] `POST /evaluate` — returns `{"status": ...}`

### waiting_room.py

- [x] `POST /{waiting_room_id}/student_to_exam` — returns `{"message": ...}`

### subject.py

- [x] `POST /{subject_id}/students` — returns `{"message": ...}`
- [x] `POST /{subject_id}/professors` — returns `{"message": ...}`
- [x] `PUT /{subject_id}/professors/{professor_id}` — returns `{"message": ...}`

### topic.py

- [x] `DELETE /{id}` — returns `{"message": ...}`

### question_option.py

- [x] `DELETE /{id}` — returns `{"message": ...}`

## Other

- [x] `GET /debug/token-info` — returns `User` model but has no `response_model`
- [x] `POST /{subject_id}/XML` — has `response_model=dict`, too loose, needs a proper schema

## Rename `StudentInfo` in `subject.py`

- [ ] `StudentInfo` in `subject.py` is used for both students and professors — rename to `KeycloakUserInfo` (or similar) to better reflect its purpose

## Ugly auto-generated schema names in docs

- [ ] `POST /evaluate` — uses `UploadFile = File(...)` directly, generates `Body_evaluate_exam_omr_api_exams_evaluate_post`
- [ ] `POST /exam/{exam_config_id}/student_list` — same issue, generates `Body_store_student_list_api_exams_exam__exam_config_id__student_list_post`

## VER ISTO

- See subjects/{id}/students. Not used anymore const useGetUcStudents(use-ucs.ts) refers the endpoint but is not used.
