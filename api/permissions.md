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
| `manager` | Platform administrators | Global - all subjects |
| `professor` | Teaching staff | Subject-specific via groups |
| `student` | Students | Subject-specific via groups |

---

### Manager Role

**Realm Role:** `manager`

Managers have **full access** to all endpoints and all subjects. They bypass group-based restrictions.

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
| `/api/subjects/{id}` | GET | Get any subject |
| `/api/subjects/{id}` | PUT | Update any subject |
| `/api/subjects/{id}` | DELETE | Delete any subject |
| `/api/subjects/{id}/students` | GET | View enrolled students |
| `/api/subjects/{id}/professors` | GET | View enrolled professors |
| `/api/subjects/{id}/regent` | GET | View subject regent |
| `/api/subjects/{id}/students` | POST | Add students to subject |
| `/api/subjects/{id}/professors` | POST | Add professor to subject |
| `/api/subjects/{id}/professors/{prof_id}` | PUT | Update professor permissions |
| `/api/subjects/{id}/professors/{prof_id}` | DELETE | Remove professor from subject |
| `/api/subjects/{id}/topics` | GET | Get all topics with question counts |
| `/api/subjects/{id}/topics-list` | GET | Get topics list |
| `/api/subjects/{id}/all-questions` | GET | Get all questions |
| `/api/topics/` | POST | Create topics |
| `/api/topics/{id}` | PUT | Update topics |
| `/api/topics/{id}` | DELETE | Delete topics |
| `/api/questions/` | POST | Create questions |
| `/api/questions/{id}` | GET | Get question |
| `/api/questions/{id}` | PUT | Update question |
| `/api/questions/{id}` | DELETE | Delete question |
| `/api/questions/{id}/question-options` | GET | Get question options |
| `/api/question-options/` | POST | Create question options |
| `/api/question-options/{id}` | PUT | Update option |
| `/api/question-options/{id}` | DELETE | Delete option |
| `/api/exams/generate` | POST | Generate exams |
| `/api/exams/subject/{id}/configs` | GET | Get exam configs |

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
| `/api/subjects/{id}/students` | POST | `/add_students`, Manager, Regent | Add students |
| `/api/subjects/{id}/professors` | POST | Manager, Regent | Add professor |
| `/api/subjects/{id}/professors/{prof_id}` | PUT | Manager, Regent | Update professor permissions |
| `/api/subjects/{id}/professors/{prof_id}` | DELETE | Manager, Regent | Remove professor |
| `/api/subjects/{id}/topics` | GET | Any subject group | Get topics |
| `/api/subjects/{id}/topics-list` | GET | Any subject group | Get topics list |
| `/api/subjects/{id}/all-questions` | GET | Any subject group | Get all questions |
| `/api/topics/` | POST | `/edit_topics`, Regent | Create topics |
| `/api/topics/{id}` | PUT | `/edit_topics`, Regent | Update topics |
| `/api/topics/{id}` | DELETE | `/edit_topics`, Regent | Delete topics |
| `/api/questions/` | POST | `/edit_questions`, Regent | Create questions |
| `/api/questions/{id}` | GET | Any subject group | Get question |
| `/api/questions/{id}` | PUT | `/edit_questions`, Regent | Update question |
| `/api/questions/{id}` | DELETE | `/edit_questions`, Regent | Delete question |
| `/api/questions/{id}/question-options` | GET | Any subject group | Get question options |
| `/api/question-options/` | POST | `/edit_questions`, Regent | Create options |
| `/api/question-options/{id}` | PUT | `/edit_questions`, Regent | Update option |
| `/api/question-options/{id}` | DELETE | `/edit_questions`, Regent | Delete option |
| `/api/exams/generate` | POST | `/generate_exams` | Generate exams |
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
| `/api/subjects/{id}/topics` | GET | Get topics |
| `/api/subjects/{id}/topics-list` | GET | Get topics list |
| `/api/subjects/{id}/all-questions` | GET | View questions (if permitted) |
| `/api/topics/` | GET | List all topics |
| `/api/topics/{id}` | GET | Get topic details |
| `/api/questions/{id}` | GET | Get question (view only) |
| `/api/questions/{id}/question-options` | GET | View question options |
| `/api/exams/subject/{id}/configs` | GET | View exam configs |

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

Same as professors with **all permission groups** automatically granted for their subject.

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
| `/api/subjects/{id}` | GET | Subject group member | Get subject by ID |
| `/api/subjects/{id}` | PUT | `manager` role | Update subject |
| `/api/subjects/{id}` | DELETE | `manager` role | Delete subject |
| `/api/subjects/{id}/students` | GET | `manager`, `/regent`, `/professors` | View students |
| `/api/subjects/{id}/professors` | GET | `manager`, `/regent`, `/professors` | View professors |
| `/api/subjects/{id}/regent` | GET | Subject group member | View regent |
| `/api/subjects/{id}/students` | POST | `manager`, `/regent`, `/add_students` | Add students |
| `/api/subjects/{id}/professors` | POST | `manager`, `/regent` | Add professor |
| `/api/subjects/{id}/professors/{prof_id}` | PUT | `manager`, `/regent` | Update professor permissions |
| `/api/subjects/{id}/professors/{prof_id}` | DELETE | `manager`, `/regent` | Remove professor |
| `/api/subjects/{id}/topics` | GET | Subject group member | Get topics with question counts |
| `/api/subjects/{id}/topics-list` | GET | Subject group member | Get topics list |
| `/api/subjects/{id}/all-questions` | GET | Subject group member | Get all questions and options |

---

### Topic Endpoints (`/api/topics/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/topics/` | POST | `/edit_topics`, Regent | Create topic |
| `/api/topics/` | GET | Authenticated | List all topics |
| `/api/topics/{id}` | GET | Authenticated | Get topic by ID |
| `/api/topics/{id}` | PUT | `/edit_topics`, Regent | Update topic |
| `/api/topics/{id}` | DELETE | `/edit_topics`, Regent | Delete topic |

---

### Question Endpoints (`/api/questions/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/questions/` | POST | `/edit_questions`, Regent | Create questions |
| `/api/questions/{subject_id}/XML` | POST | `/edit_questions`, Regent | Create questions from XML |
| `/api/questions/{id}` | GET | Authenticated | Get question by ID |
| `/api/questions/{id}` | PUT | `/edit_questions`, Regent | Update question |
| `/api/questions/{id}` | DELETE | `/edit_questions`, Regent | Delete question |
| `/api/questions/{id}/question-options` | GET | Authenticated | Get question options |

---

### Question Option Endpoints (`/api/question-options/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/question-options/` | POST | `/edit_questions`, Regent | Create question options |
| `/api/question-options/{id}` | PUT | `/edit_questions`, Regent | Update option |
| `/api/question-options/{id}` | DELETE | `/edit_questions`, Regent | Delete option |

---

### Exam Endpoints (`/api/exams/*`)

| Endpoint | Method | Required Permission | Description |
|----------|--------|---------------------|-------------|
| `/api/exams/generate` | POST | `/generate_exams` | Generate exam PDFs |
| `/api/exams/subject/{id}/configs` | GET | Subject group member | Get exam configurations |

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

### Role-Based Check

```python
from src.core.deps import require_manager

@router.post("/", dependencies=[Depends(require_manager)])
async def create_subject():
    # Only managers can access
```

### Group-Based Check

```python
from src.core.deps import require_group

@router.post("/students")
async def add_students(
    user: User = Depends(require_group("/s123/add_students"))
):
    # Only users in s123/add_students group can access
```

### Custom Permission Check

```python
from src.core.deps import get_current_user_info

@router.get("/{subject_id}/students")
async def get_students(
    subject_id: int,
    user_info: User = Depends(get_current_user_info)
):
    roles = user_info.realm_roles
    groups = user_info.groups

    if not ("manager" in roles or
            any(g.endswith(f"s{subject_id}/regent") for g in groups) or
            any(g.endswith(f"s{subject_id}/professors") for g in groups)):
        raise HTTPException(status_code=403, detail="Access denied")
```

---

## Authentication Flow

1. **User logs in** via Keycloak (OIDC)
2. **Keycloak returns JWT** with roles and groups
3. **Frontend includes token** in `Authorization: Bearer <token>` header
4. **API verifies token** using `get_current_user_info` dependency
5. **Permission checks** validate roles/groups before executing endpoint

---

## Error Responses

| Status Code | Meaning | Response |
|-------------|---------|----------|
| `401` | Not authenticated | `{"detail": "Not authenticated"}` |
| `401` | Invalid token | `{"detail": "Invalid token"}` |
| `403` | Missing role | `{"detail": "Requires {role} role"}` |
| `403` | Missing group | `{"detail": "Requires membership in group {group}"}` |
| `403` | Custom denial | `{"detail": "Access denied"}` |

---

## Summary Tables

### Quick Reference: Who Can Access What

| Action | Manager | Regent | Professor | Student |
|--------|:-------:|:------:|:---------:|:-------:|
| Create subjects | ✅ | ❌ | ❌ | ❌ |
| Update/Delete any subject | ✅ | ❌ | ❌ | ❌ |
| Create users | ✅ | ❌ | ❌ | ❌ |
| Create topics (own subject) | ✅ | ✅ | ⚠️ | ❌ |
| Create questions (own subject) | ✅ | ✅ | ⚠️ | ❌ |
| Add students (own subject) | ✅ | ✅ | ⚠️ | ❌ |
| Generate exams (own subject) | ✅ | ✅ | ⚠️ | ❌ |
| View own subjects | ✅ | ✅ | ✅ | ✅ |
| View questions | ✅ | ✅ | ✅ | ⚠️ |

**Legend:**
- ✅ = Full access
- ⚠️ = Requires specific permission group
- ❌ = No access

---

## Adding New Permissions

To add a new permission group:

1. **Add group to Keycloak** when creating subject:
```python
subgroups = [
    "regent", "students", "professors",
    "edit_topics", "edit_questions",
    "view_question_bank", "add_students",
    "generate_exams", "view_grades",
    "auto_correct_exams",
    "NEW_PERMISSION"  # Add here
]
```

2. **Create dependency** in `src/core/deps.py`:
```python
def require_new_permission(subject_id: str):
    group_name = f"/s{subject_id}/NEW_PERMISSION"
    return require_group(group_name)
```

3. **Apply to endpoint**:
```python
@router.post("/new-feature", dependencies=[Depends(require_new_permission)])
async def new_feature():
    ...
```
