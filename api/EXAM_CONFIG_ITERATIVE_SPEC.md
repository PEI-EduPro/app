# Exam Config Iterative Workflow Specification

## Objective
Refactor the `ExamConfig` lifecycle to be more iterative, guiding the user (regent) step-by-step through the exam process. This involves renaming the existing state field, introducing a rigid state machine with distinct phases, and enforcing rules based on the current state.

## State Machine Definition

The `ExamConfig` will transition through the following states sequentially (with some exceptions for late photo submissions).

1. **`preparing`** (Initial State)
   - **Allowed Actions:** Edit vigilantes (add/remove). Configure the exam details. Delete the `exam_config`.
   - **Transition:** Regent manually "starts" the exam -> transitions to `running`.

2. **`running`**
   - **Allowed Actions:** Regent and vigilant professors associate students with exams.
   - **Transition:** Regent manually "closes" the exam -> transitions to `closed_and_capture`.

3. **`closed_and_capture`**
   - **Allowed Actions:** Upload/capture pictures of the exams for automatic correction.
   - **Constraints:** NO MORE associations between students and exams are permitted.
   - **Transition:** Regent manually signifies the end of the initial capture phase -> transitions to `warning_handling`.

4. **`warning_handling`**
   - **Allowed Actions:** Regent resolves warnings raised during association (e.g., multiple students to one exam, one exam to multiple students) and capture (e.g., photo taken without associated student). Regent can also upload late exam pictures.
   - **Transition Constraints:** Can only transition if all warnings are resolved.
   - **Transition:** Regent manually advances the process -> transitions to `validation`.

5. **`validation`**
   - **Allowed Actions:** Regent validates the OMR correction for each exam. Regent can upload late exam pictures.
   - **Transition Constraints:** All exams that have *associated pictures* must be validated.
   - **Transition:** Regent manually advances the process -> transitions to `completed`.

6. **`completed`**
   - **Allowed Actions:** Notify students of their grades (send emails). Regent can delete the `exam_config`. Regent can upload late exam pictures.

### Edge Case: Late Photo Submissions
During the `warning_handling`, `validation`, and `completed` states, the regent can submit additional photos.
- If a late photo **raises a warning** (e.g., no associated student), the `ExamConfig` state immediately reverts to `warning_handling`.
- If a late photo **does not raise a warning**, the `ExamConfig` state reverts to `validation` (so the new exam can be validated).

## Constraints & Business Logic Updates

- **Deletion (`DELETE /exam_configs/{id}`):** Can only be performed if the state is `preparing` or `completed`.
- **Associations:** Can only be created/modified when the state is `running`.
- **Get Information (`GET /exam_configs/{id}`):** The response must include:
  - `total_exams`: Always returned (count of all exams generated).
  - `associated_exams_count`: Only returned if state >= `running` (count of exams linked to a student).
  - `pictured_exams_count`: Only returned if state >= `closed_and_capture` (count of exams with an uploaded/processed image).

---

## Task Breakdown

### 1. Database & Models
- [x] **Model Update:** In `src/models/exam_config.py`, rename the `session_state` field to `state`.
- [x] **Enum Update:** Create or update the `ExamState` Enum with the new values: `preparing`, `running`, `closed_and_capture`, `warning_handling`, `validation`, `completed`.
- [x] **Alembic Migration:** Generate and review an Alembic migration to rename the column and update the Enum type in PostgreSQL.

### 2. Schemas
- [x] Update `ExamConfigRead` (or equivalent schema) to include the new `state` field.
- [x] Add computed properties or fields to `ExamConfigRead` for `total_exams`, `associated_exams_count`, `pictured_exams_count`. Make the last two `Optional` and populate them based on the state.
- [x] Update `ExamConfigCreate` and `ExamConfigUpdate` schemas to reflect the new state naming and remove any manual state setting that shouldn't be exposed directly.

### 3. Services
- [x] **State Transition Logic:** Create a service function to handle manual state transitions (e.g., `transition_exam_config_state(exam_config_id, target_state)`). This function must validate the business rules (e.g., checking for unresolved warnings before moving to `validation`, or checking if all pictured exams are validated before moving to `completed`).
- [x] **Counters Logic:** In the `get_exam_config` service, query the database to calculate `total_exams`, `associated_exams_count`, and `pictured_exams_count` based on the current state.
- [x] **Late Photo Upload Logic:** Update the `evaluate_exam` (or OMR processing service) to check the current `ExamConfig` state. If it is `warning_handling`, `validation`, or `completed`, implement the logic to revert the state based on whether warnings were generated.

### 4. Routers & Endpoints
- [ ] **New Endpoint:** `POST /exam_configs/{id}/state` (or similar) to allow the regent to advance the state.
- [ ] **Delete Endpoint:** Update `DELETE /exam_configs/{id}` to enforce the `preparing` or `completed` state restriction.
- [ ] **Association Endpoint:** Update the endpoints that link students to exams to ensure they return a 403/400 if the state is not `running`.
- [ ] **Validation Endpoint:** Ensure endpoints related to validating exams function correctly with the new states.
