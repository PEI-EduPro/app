# TODO - fix/missing-parametrization

## Missing `response_model` on endpoints that return data

### exam.py
- [ ] `POST /generate` — returns ZIP, skip
- [ ] `POST /exam/{exam_config_id}/student_list` — returns `{"message": ...}`
- [ ] `POST /evaluate` — returns `{"status": ...}`

### waiting_room.py
- [ ] `POST /{waiting_room_id}/student_to_exam` — returns `{"message": ...}`

### subject.py
- [ ] `POST /{subject_id}/students` — returns `{"message": ...}`
- [ ] `POST /{subject_id}/professors` — returns `{"message": ...}`
- [ ] `PUT /{subject_id}/professors/{professor_id}` — returns `{"message": ...}`

### topic.py
- [ ] `DELETE /{id}` — returns `{"message": ...}`

### question_option.py
- [ ] `DELETE /{id}` — returns `{"message": ...}`

## Other
- [ ] `GET /debug/token-info` — returns `User` model but has no `response_model`
