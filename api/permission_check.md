## Authorization Guide: Checking User Permissions in the API

This guide explains how to verify if the currently authenticated user has permission to perform a specific action within the API. This is handled by checking the user's roles and group memberships, which are retrieved from their JWT access token obtained from Keycloak.

### Core Concept

The application relies on Keycloak for user identity and permissions. When a user logs in, Keycloak issues a JWT access token. This token contains claims, including the user's roles and group memberships relevant to the `api-backend` client and the `master` realm. The API extracts this information from the token to decide if the user can access a particular endpoint or perform an action.

### Key Components

1.  **JWT Token:** Obtained by the client (e.g., frontend) using the user's credentials and the `api-backend` client details. Passed to the API via the `Authorization: Bearer <token>` header.
2.  **`get_current_user_info`:** A dependency function (defined in `src/core/deps.py`) that verifies the token's signature and expiration, extracts user information (ID, username, roles, groups), and returns it. This dependency is implicitly called when you use `current_user_info: dict = Depends(get_current_user_info)` in an endpoint.
3.  **Dependency Functions:** Pre-built functions in `src/core/deps.py` that check specific conditions within the `current_user_info` (e.g., having a specific role or being in a specific group). These dependencies are applied directly to endpoints using `dependencies=[Depends(...)]` or called within the endpoint function body.
4.  **Groups for Fine-Grained Permissions:** Permissions like "is regent of subject X" or "can edit questions for subject Y" are managed using Keycloak groups with a structured naming convention (e.g., `/s101/regent`, `/s102/edit_questions`).

### How to Check Permissions

#### 1. Checking Realm Roles (Manager, Professor, Student)

Use the pre-defined dependency functions `require_manager`, `require_professor`, or `require_student`.

**Usage:**

```python
from fastapi import APIRouter, Depends
from src.core.deps import require_manager, get_current_user_info # Import the required dependency

router = APIRouter()

# Example: Only managers can access this endpoint
@router.post("/admin/some-action", dependencies=[Depends(require_manager)])
async def admin_action():
    # This code runs only if the user has the 'manager' role
    return {"message": "Admin action performed"}

# Example: Get current user info within the endpoint after role check
@router.get("/dashboard/professor", dependencies=[Depends(require_professor)])
async def professor_dashboard(current_user_info: dict = Depends(get_current_user_info)):
    # This code runs only if the user has the 'professor' role
    # current_user_info contains details like ID, username, roles, groups
    return {"dashboard_type": "professor", "user": current_user_info["username"]}
```

**How it Works:**

*   `dependencies=[Depends(require_manager)]` is added to the endpoint decorator.
*   `require_manager` is an async function that takes `get_current_user_info` as a dependency.
*   It fetches the `current_user_info`, checks if `"manager"` is in `current_user_info["realm_roles"]`.
*   If the role is present, the main endpoint function executes.
*   If the role is *not* present, it raises an `HTTPException` (403 Forbidden), and the main endpoint function does *not* run.

#### 2. Checking Subject-Specific Group Permissions (Regent, Edit Questions, etc.)

Use the pre-defined dependency factory functions like `require_subject_regent`, `require_edit_question_bank`, `require_add_students`, etc. These functions require a `subject_id` as an argument.

**Usage:**

```python
from fastapi import APIRouter, Depends, Path # Import Path for path parameters
from src.core.deps import require_subject_regent, require_edit_question_bank, get_current_user_info

router = APIRouter()

# Example: Only the regent of subject 's101' can access this
@router.put("/subjects/s101/config", dependencies=[Depends(require_subject_regent("s101"))])
async def update_subject_config_s101():
    # Code runs only if user is in group '/s101/regent'
    return {"message": "Subject s101 config updated"}

# Example: Using a path parameter for subject ID
@router.post("/subjects/{subject_id}/topics", dependencies=[Depends(require_subject_regent)]) # Note: Pass the factory, not a call
async def create_topic_for_subject(
    subject_id: str = Path(...), # Get subject_id from the path
    current_user_info: dict = Depends(get_current_user_info) # Get user info
):
    # Manually call the check inside the function using the path parameter
    # You might need a slightly different approach for dynamic IDs in dependencies
    # Option 1: Manual check inside the function (see below)
    # Option 2: A custom dependency that extracts subject_id from path/params and checks
    # For now, let's assume a helper function or a custom dependency handles the dynamic check
    pass

# Example: Check permission based on subject_id from the path parameter (Manual Check Inside Function)
from src.core.deps import get_current_user_info # Import the base dependency

def user_has_subject_permission(current_user_info: dict, subject_id: str, permission: str):
    """Helper function to check if user has a specific permission for a subject."""
    required_group = f"/s{subject_id}/{permission}"
    return required_group in current_user_info.get("groups", [])

@router.post("/subjects/{subject_id}/topics")
async def create_topic_for_subject(
    subject_id: str = Path(...),
    current_user_info: dict = Depends(get_current_user_info) # Get user info first
):
    # Check if user is regent for the specific subject
    if not user_has_subject_permission(current_user_info, subject_id, "regent"):
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail=f"User does not have regent permission for subject {subject_id}"
         )
    # If check passes, proceed with the logic
    return {"message": f"Topic created for subject {subject_id}"}

# Example: Using a factory function dependency (requires custom implementation)
# This is a more elegant way but requires creating a dependency that can access path params
# src/core/deps.py would need something like:
# def require_subject_permission(permission: str):
#     def check_permission(
#         subject_id: str = Path(...), # This is tricky, Path(...) might not work directly in a sub-dependency
#         current_user_info: dict = Depends(get_current_user_info)
#     ):
#         required_group = f"/s{subject_id}/{permission}"
#         if required_group not in current_user_info.get("groups", []):
#              raise HTTPException(
#                  status_code=status.HTTP_403_FORBIDDEN,
#                  detail=f"User lacks permission '{permission}' for subject {subject_id}"
#              )
#         return current_user_info # Return user info if check passes
#     return check_permission
#
# Then in the router:
# @router.post("/subjects/{subject_id}/topics")
# async def create_topic_for_subject(
#     subject_id: str = Path(...),
#     current_user_info: dict = Depends(require_subject_permission("regent")) # This is the tricky part
# ):
#     # If we get here, permission is granted
#     return {"message": f"Topic created for subject {subject_id}"}
#
# The manual check (first example under this heading) is often simpler for dynamic parameters.

# Example: Using the factory for a fixed subject (e.g., defined by a config or environment)
# If subject_id is fixed or can be determined without a path param in the dependency itself:
# @router.post("/fixed-subject-topics", dependencies=[Depends(require_edit_question_bank("101"))])
# async def create_topic_fixed_subject():
#     # Code runs only if user is in group '/s101/edit_question_bank'
#     return {"message": "Topic created in fixed subject"}
```

**How it Works (for `require_subject_regent(subject_id)`):**

*   `dependencies=[Depends(require_subject_regent("s101"))]` is added to the endpoint.
*   `require_subject_regent` is a *factory function* that takes a `subject_id` (e.g., "101") and *returns* a dependency function.
*   The returned dependency function takes `get_current_user_info` as its dependency.
*   It fetches the `current_user_info`, constructs the required group name (e.g., `/s101/regent`), and checks if this group name is in `current_user_info["groups"]`.
*   If the group membership exists, the main endpoint function executes.
*   If the group membership is *not* present, it raises an `HTTPException` (403 Forbidden).

### Summary for Developers

1.  **Identify the required permission:** Does the user need a specific realm role (manager, professor, student) or a subject-specific group permission (regent, edit_questions, etc.)?
2.  **Choose the appropriate dependency:**
    *   For roles: Use `require_manager`, `require_professor`, `require_student`.
    *   For subject groups (fixed ID): Use `require_subject_regent(subject_id)`, `require_edit_question_bank(subject_id)`, etc.
    *   For subject groups (dynamic ID from path): Consider using a manual check within the function using `get_current_user_info` and helper functions, or explore creating a custom dependency that can access path parameters.
3.  **Apply the dependency:** Add `dependencies=[Depends(your_chosen_dependency)]` to the FastAPI endpoint decorator (e.g., `@router.get(...)`, `@router.post(...)`).
4.  **Access User Info (Optional):** If you need to access the user's ID, username, or other details *within* the endpoint function after authorization has been checked, use `current_user_info: dict = Depends(get_current_user_info)` as a parameter in your endpoint function.

By following this pattern, you ensure that only users with the correct permissions can access specific API endpoints, leveraging Keycloak for centralized and secure authorization.