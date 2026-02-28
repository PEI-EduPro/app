# Permissions & Access Control Documentation

## Overview

This document details the role-based access control (RBAC) system for the Education Platform API. Access is controlled through:

1. **Realm Roles** - Global roles assigned to users in Keycloak
2. **Subject Groups** - Per-subject groups with specific permissions

---

## Part 1: Roles and Their Permissions

### User Roles

| Role | Description | Scope |
|------|-------------|-------|
| `manager` | Platform administrators | Global - all subjects, but only for administrative actions |
| `professor` | Teaching staff | Subject-specific via groups |
| `student` | Students | Subject-specific via groups |

---

### Manager Role

**Realm Role:** `manager`

Managers have **administrative access** to the platform. They can manage subjects, users, enrollments, and roles. However, **they do not have implicit access to subject content** (topics, questions, exams).

#### Endpoints Accessible by Managers

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/me` | GET | Get own user info |
| `/api/users/create` | POST | Create new users |
| `/api/users/professors` | GET | List all professors |
| `/api/users/students` | GET | List all students |
| `/api/users/debug/token-info` | GET | Debug token information |
| `/api/subjects/` | POST | Create new subjects |
| `/api/subjects/` | GET | List all subjects |
| `/api/subjects/{id}` | PUT | Update any subject |
| `/api/subjects/{id}` | DELETE | Delete any subject |
| `/api/subjects/{id}/students` | GET | View enrolled students |
| `/api/subjects/{id}/professors` | GET | View enrolled professors |
| `/api/subjects/{id}/students` | POST | Add students to subject |
| `/api/subjects/{id}/professors` | POST | Add professor to subject |
| `/api/subjects/{id}/professors/{prof_id}` | PUT | Update professor permissions |
| `/api/subjects/{id}/professors/{prof_id}` | DELETE | Remove professor from subject |

---

### Professor Role

**Realm Role:** `professor`

Professors have **subject-specific access** based on group membership. They must be explicitly added to subjects.

#### Subject Groups for Professors

| Group | Path | Permissions |
|-------|------|-------------|
| Professors (Base) | `/s{subject_id}/professors` | View students, view professors, view regent |
| Edit Topics | `/s{subject_id}/edit_topics` | Create, update, delete topics |
| Edit Questions | `/s{subject_id}/edit_questions` | Create, update, delete questions |
| View Question Bank | `/s{subject_id}/view_question_bank` | View all questions in subject |
| Add Students | `/s{subject_id}/add_students` | Add students to subject |
| Generate Exams | `/s{subject_id}/generate_exams` | Generate exams |
| View Grades | `/s{subject_id}/view_grades` | View student grades |
| Auto Correct Exams | `/s{subject_id}/auto_correct_exams` | Auto-correct exams |

#### Endpoints Accessible by Professors

| Endpoint | Method | Required Group | Description |
|----------|--------|----------------|-------------|
| `/api/users/me` | GET | — | Get own user info |
| `/api/users/professors` | GET | — | List all professors |
| `/api/subjects/` | GET | Any subject group | List subjects user belongs to |
| `/api/subjects/{id}` | GET | Any subject group | Get subject details |
| `/api/subjects/{id}/students` | GET | `/professors`, `/regent` | View enrolled students |
| `/api/subjects/{id}/professors` | GET | `/professors`, `/regent` | View enrolled professors |
| `/api/subjects/{id}/regent` | GET | Any subject group | View subject regent |
| `/api/subjects/{id}/topics` | GET | `/view_question_bank`, `/regent` | Get topics |
| `/api/subjects/{id}/topics-list` | GET | `/view_question_bank`, `/regent` | Get topics list |
| `/api/subjects/{id}/all-questions` | GET | `/view_question_bank`, `/regent` | Get all questions |
| `/api/topics/` | POST | `/edit_topics`, `/regent` | Create topics |
| `/api/topics/{id}` | PUT | `/edit_topics`, `/regent` | Update topics |
| `/api/topics/{id}` | DELETE | `/edit_topics`, `/regent` | Delete topics |
| `/api/questions/` | POST | `/edit_questions`, `/regent` | Create questions |
| `/api/questions/{id}` | GET | `/view_question_bank`, `/regent` | Get question |
| `/api/questions/{id}` | PUT | `/edit_questions`, `/regent` | Update question |
| `/api/questions/{id}` | DELETE | `/edit_questions`, `/regent` | Delete question |
| `/api/questions/{id}/question-options` | GET | `/view_question_bank`, `/regent` | Get question options |
| `/api/question-options/` | POST | `/edit_questions`, `/regent` | Create options |
| `/api/question-options/{id}` | PUT | `/edit_questions`, `/regent` | Update option |
| `/api/question-options/{id}` | DELETE | `/edit_questions`, `/regent` | Delete option |
| `/api/exams/generate` | POST | `/generate_exams`, `/regent` | Generate exams |
| `/api/exams/subject/{id}/configs` | GET | Any subject group | Get exam configs |

---

### Student Role

**Realm Role:** `student`

Students have **read-only access** to subjects they are enrolled in.

#### Subject Groups for Students

| Group | Path | Permissions |
|-------|------|-------------|
| Students | `/s{subject_id}/student` | Basic student access |

#### Endpoints Accessible by Students

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/me` | GET | Get own user info |
| `/api/users/students` | GET | List all students |
| `/api/subjects/` | GET | List enrolled subjects |
| `/api/subjects/{id}` | GET | Get subject details |

---

### Regent (Special Professor Role)

**Not a realm role** - Regents are professors assigned to the `/s{subject_id}/regent` group for a specific subject.

#### Regent Permissions

Regents have **full management** over their assigned subject:

| Permission | Description |
|------------|-------------|
| Create topics | Create new topics in subject |
| Edit topics | Modify existing topics |
| Delete topics | Remove topics |
| Create questions | Add new questions |
| Edit questions | Modify questions |
| Delete questions | Remove questions |
| Add students | Enroll students in subject |
| Manage professors | Add/remove professors, set permissions |
| View all | View students, professors, regent info |

#### Endpoints Accessible by Regents

Same as professors with **all permission groups** directly evaluated via `verify_permission`.

---

## Part 2: Endpoints and Required Permissions

### Health & Public Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/health` | GET | Public | Health check |
| `/` | GET | Public | API welcome message |
| `/api/docs` | GET | Public | Swagger UI documentation |
| `/redoc` | GET | Public | ReDoc documentation |

---

### User Endpoints (`/api/users/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/users/me` | GET | Authenticated | Get current user info |
| `/api/users/create` | POST | `manager` role | Create new user |
| `/api/users/professors` | GET | Authenticated | List all professors |
| `/api/users/students` | GET | Authenticated | List all students |
| `/api/users/debug/token-info` | GET | `manager` role | Debug token information |

---

### Subject Endpoints (`/api/subjects/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/subjects/` | POST | `manager` role | Create new subject |
| `/api/subjects/` | GET | Authenticated | List accessible subjects |
| `/api/subjects/{id}` | GET | Subject group member (`/s{id}`) | Get subject by ID |
| `/api/subjects/{id}` | PUT | `manager` role | Update subject |
| `/api/subjects/{id}` | DELETE | `manager` role | Delete subject |
| `/api/subjects/{id}/students` | GET | `manager`, `/s{id}/professors`, `/s{id}/regent` | View students |
| `/api/subjects/{id}/professors` | GET | `manager`, `/s{id}/professors`, `/s{id}/regent` | View professors |
| `/api/subjects/{id}/regent` | GET | Subject group member (`/s{id}`) | View regent |
| `/api/subjects/{id}/students` | POST | `manager`, `/s{id}/add_students`, `/s{id}/regent` | Add students |
| `/api/subjects/{id}/professors` | POST | `manager`, `/s{id}/regent` | Add professor |
| `/api/subjects/{id}/professors/{prof_id}` | PUT | `manager`, `/s{id}/regent` | Update professor permissions |
| `/api/subjects/{id}/professors/{prof_id}` | DELETE | `manager`, `/s{id}/regent` | Remove professor |
| `/api/subjects/{id}/topics` | GET | `/s{id}/view_question_bank`, `/s{id}/regent` | Get topics with question counts |
| `/api/subjects/{id}/topics-list` | GET | `/s{id}/view_question_bank`, `/s{id}/regent` | Get topics list |
| `/api/subjects/{id}/all-questions` | GET | `/s{id}/view_question_bank`, `/s{id}/regent` | Get all questions and options |

---

### Topic Endpoints (`/api/topics/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/topics/` | POST | `/s{id}/edit_topics`, `/s{id}/regent` | Create topic |
| `/api/topics/{id}` | GET | Subject group member (`/s{id}`) | Get topic by ID |
| `/api/topics/{id}` | PUT | `/s{id}/edit_topics`, `/s{id}/regent` | Update topic |
| `/api/topics/{id}` | DELETE | `/s{id}/edit_topics`, `/s{id}/regent` | Delete topic |

---

### Question Endpoints (`/api/questions/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/questions/` | POST | `/s{id}/edit_questions`, `/s{id}/regent` | Create questions |
| `/api/questions/{subject_id}/XML` | POST | `/s{id}/edit_questions`, `/s{id}/regent` | Create questions from XML |
| `/api/questions/{id}` | GET | `/s{id}/view_question_bank`, `/s{id}/regent` | Get question by ID |
| `/api/questions/{id}` | PUT | `/s{id}/edit_questions`, `/s{id}/regent` | Update question |
| `/api/questions/{id}` | DELETE | `/s{id}/edit_questions`, `/s{id}/regent` | Delete question |
| `/api/questions/{id}/question-options` | GET | `/s{id}/view_question_bank`, `/s{id}/regent` | Get question options |

---

### Question Option Endpoints (`/api/question-options/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/question-options/` | POST | `/s{id}/edit_questions`, `/s{id}/regent` | Create question options |
| `/api/question-options/{id}` | PUT | `/s{id}/edit_questions`, `/s{id}/regent` | Update option |
| `/api/question-options/{id}` | DELETE | `/s{id}/edit_questions`, `/s{id}/regent` | Delete option |

---

### Exam Endpoints (`/api/exams/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/exams/generate` | POST | `/s{id}/generate_exams`, `/s{id}/regent` | Generate exam PDFs |
| `/api/exams/subject/{id}/configs` | GET | Subject group member (`/s{id}`) | Get exam configurations |

---

## Group Hierarchy Structure

```
s{subject_id}/                    # Base subject group
├── regent/                       # Subject regent (full control)
├── students/                     # Enrolled students
├── professors/                   # Base professors group
├── edit_topics/                  # Can create/edit/delete topics
├── edit_questions/               # Can create/edit/delete questions
├── view_question_bank/           # Can view all questions
├── add_students/                 # Can add students to subject
├── generate_exams/               # Can generate exams
├── view_grades/                  # Can view student grades
└── auto_correct_exams/           # Can auto-correct exams
```

---

## Permission Check Implementation

### Custom Permission Check

Permissions are enforced using the `verify_permission` function, checking if the authenticated user has one of a required list of permissions. 

```python
from src.core.deps import get_current_user_info, verify_permission

@router.post("/{subject_id}/students")
async def add_students(
    subject_id: int,
    user_info: User = Depends(get_current_user_info)
):
    # Checking if the user possesses `/s{id}/add_students`, `/s{id}/regent`, or is a global `manager`
    verify_permission(
        user_info, 
        [f"/s{subject_id}/add_students", f"/s{subject_id}/regent"], 
        allow_manager=True
    )
```

```python
from src.core.deps import get_current_user_info, verify_permission

@router.post("/topics/")
async def create_topic(
    topic_data: TopicCreate,
    user_info: User = Depends(get_current_user_info)
):
    # Only checks explicit groups (Managers are implicitly denied unless they belong to the groups)
    verify_permission(
        user_info, 
        [f"/s{topic_data.subject_id}/edit_topics", f"/s{topic_data.subject_id}/regent"]
    )
```

---

## Authentication Flow

1. **User logs in** via Keycloak (OIDC)
2. **Keycloak returns JWT** with roles and groups
3. **Frontend includes token** in `Authorization: Bearer <token>` header
4. **API verifies token** using `get_current_user_info` dependency
5. **Permission checks** validate roles/groups before executing endpoint using `verify_permission`

---

## Error Responses

| Status Code | Meaning | Response |
|-------------|---------|----------|
| `401` | Not authenticated | `{"detail": "Not authenticated"}` |
| `401` | Invalid token | `{"detail": "Invalid token"}` |
| `403` | Custom denial | `{"detail": "Access denied"}` |

---

## Summary Tables

### Quick Reference: Who Can Access What

| Action | Manager | Regent | Professor | Student |
|--------|:-------:|:------:|:---------:|:-------:|
| Create subjects | ✅ | ❌ | ❌ | ❌ |
| Update/Delete any subject | ✅ | ❌ | ❌ | ❌ |
| Create users | ✅ | ❌ | ❌ | ❌ |
| Add students/professors to any subject | ✅ | ✅ | ⚠️ | ❌ |
| Create topics (own subject) | ❌ | ✅ | ⚠️ | ❌ |
| Create questions (own subject) | ❌ | ✅ | ⚠️ | ❌ |
| Generate exams (own subject) | ❌ | ✅ | ⚠️ | ❌ |
| View own subjects | ✅ | ✅ | ✅ | ✅ |
| View questions | ❌ | ✅ | ✅ | ⚠️ |

**Legend:**
- ✅ = Full access
- ⚠️ = Requires specific permission group
- ❌ = No access
