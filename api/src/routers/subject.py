from typing import List, Set
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.db import get_session
from src.core.deps import require_manager, verify_regent_exists, get_current_user_info
from src.core.keycloak import keycloak_client
import logging

from src.models.subject import (
    Subject, 
    SubjectCreateRequest, 
    SubjectCreateResponse, 
    SubjectRead,
    SubjectUpdate,
    StudentAddRequest,
    StudentInfo,
    ProfessorAddRequest,
    ProfessorUpdateRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=SubjectCreateResponse, dependencies=[Depends(require_manager)])
async def create_subject_endpoint(
    subject_data: SubjectCreateRequest, # Receive the request body data
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new subject in the database and its corresponding Keycloak groups.
    Assigns the specified user as the regent.
    Requires the 'manager' role.
    """
    logger.info(f"Manager is attempting to create a new subject: '{subject_data.name}', assigning regent ID: {subject_data.regent_keycloak_id}")

    try:
        # 1. Verify regent exists BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have subject_data
        regent_info = await verify_regent_exists(subject_data.regent_keycloak_id)

        # 2. Create the Subject in the local database
        db_subject = Subject(name=subject_data.name)
        session.add(db_subject)
        await session.commit()
        await session.refresh(db_subject) # Get the auto-generated ID

        logger.info(f"Subject '{db_subject.name}' created in database with ID: {db_subject.id}")

        # 3. Create Keycloak groups and assign regent using the ID from the database
        success = await keycloak_client.create_subject_groups_and_assign_regent(
            subject_id=str(db_subject.id), # Use the DB ID to name the groups
            regent_keycloak_id=subject_data.regent_keycloak_id
        )

        if not success:
            # If group creation/assignment failed, consider rolling back the DB creation
            # For now, just log and raise an error
            logger.error(f"Failed to create Keycloak groups for subject {db_subject.id}. DB entry may need cleanup.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Subject created in database, but failed to create Keycloak groups."
            )

        logger.info(f"Subject '{db_subject.name}' (ID: {db_subject.id}) and Keycloak groups created successfully. Regent assigned.")

        # Return success response
        return SubjectCreateResponse(
            id=db_subject.id,
            name=db_subject.name,
            message="Subject and Keycloak groups created successfully. Regent assigned.",
            regent_username=regent_info.get('username') # Return the verified regent's username
        )

    except ValueError as ve:
        # Handle specific validation errors like regent not found (caught by verify_regent_exists)
        logger.warning(f"Validation error during subject creation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation (e.g., DB error, Keycloak error)
        logger.error(f"Failed to create subject '{subject_data.name}': {e}")
        logger.exception(e) # Log the full traceback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the subject in the database or Keycloak."
        )

@router.get("/", response_model=List[SubjectRead])
async def get_subjects(
    session: AsyncSession = Depends(get_session),
    user_info: dict = Depends(get_current_user_info)
):
    """
    Get a list of subjects the user has access to.
    - Managers: See all subjects.
    - Professors: See subjects where they are 'regent' or 'professors'.
    - Students: See subjects where they are 'students'.
    """
    user_roles = user_info.get("realm_roles", [])
    user_groups = user_info.get("groups", [])
    username = user_info.get("username")

    # 1. Manager Access: Return everything
    if "manager" in user_roles:
        logger.info(f"Manager '{username}' requesting all subjects.")
        result = await session.exec(select(Subject))
        return result.all()

    # 2. Filtered Access: Parse groups to find allowed Subject IDs
    allowed_subject_ids: Set[int] = set()
    
    # We only care about groups ending in these suffixes
    relevant_subgroups = {"regent", "professors", "students"}

    logger.debug(f"Parsing groups for user '{username}': {user_groups}")

    for group_path in user_groups:
        # Keycloak group paths usually look like "/s1/students" or "s1/students"
        # Strip leading slash for consistent processing
        clean_path = group_path.lstrip('/')
        
        parts = clean_path.split('/')
        
        # We expect format: "s{id}/{role}" -> 2 parts
        if len(parts) == 2:
            subject_part = parts[0] # e.g., "s4"
            role_part = parts[1]    # e.g., "students"

            # Check if this is a subject group (starts with 's') and a relevant role
            if subject_part.startswith('s') and role_part in relevant_subgroups:
                try:
                    # Extract the ID number (everything after 's')
                    subject_id = int(subject_part[1:])
                    allowed_subject_ids.add(subject_id)
                except ValueError:
                    # Handle cases where subject_part isn't "s" + number (e.g. "super/admin")
                    continue

    if not allowed_subject_ids:
        # User has no subject associations
        return []

    # 3. Fetch only the specific subjects from DB
    logger.info(f"User '{username}' has access to subject IDs: {allowed_subject_ids}")
    statement = select(Subject).where(Subject.id.in_(allowed_subject_ids))
    result = await session.exec(statement)
    subjects = result.all()
    
    return subjects

@router.put("/{subject_id}", response_model=SubjectRead, dependencies=[Depends(require_manager)])
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    Update a subject's name or assign a new regent.
    Only accessible by Managers.
    """
    # 1. Fetch the subject
    subject = await session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # 2. Update Name if provided
    if subject_update.name:
        subject.name = subject_update.name
        logger.info(f"Updating subject {subject_id} name to: {subject_update.name}")

    # 3. Update Regent if provided
    if subject_update.regent_keycloak_id:
        # Verify user exists first
        await verify_regent_exists(subject_update.regent_keycloak_id)
        
        success = await keycloak_client.update_subject_regent(
            subject_id=str(subject_id),
            new_regent_id=subject_update.regent_keycloak_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update regent in Keycloak."
            )

    # 4. Save DB changes
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_subject(
    subject_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a subject from the database and remove all associated Keycloak groups.
    Only accessible by Managers.
    """
    # 1. Fetch the subject
    subject = await session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # 2. Delete from Keycloak
    # We do this before DB delete. If KC fails, we might want to keep DB or retry.
    # Here we proceed but log heavily if it fails.
    kc_success = await keycloak_client.delete_subject_groups(str(subject_id))
    if not kc_success:
        logger.warning(f"Failed to fully clean up Keycloak groups for subject {subject_id}. Proceeding with DB deletion.")

    # 3. Delete from DB
    await session.delete(subject)
    await session.commit()
    
    logger.info(f"Subject {subject_id} deleted.")
    return None

@router.get("/{subject_id}/students", response_model=List[StudentInfo])
async def get_subject_students(
    subject_id: int,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all students enrolled in a subject.
    Access: Manager OR Subject Regent OR Subject Professor.
    """
    # 1. Check if Subject exists in DB
    subject = await session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # 2. Permission Check
    username = user_info.get("username")
    user_groups = user_info.get("groups", [])
    user_roles = user_info.get("realm_roles", [])
    
    # Define required group suffixes for this subject
    regent_group = f"s{subject_id}/regent"
    prof_group = f"s{subject_id}/professors"

    # Check: Is Manager? OR Is in Regent Group? OR Is in Professor Group?
    is_manager = "manager" in user_roles
    is_regent = any(g.endswith(regent_group) for g in user_groups)
    is_prof = any(g.endswith(prof_group) for g in user_groups)

    if not (is_manager or is_regent or is_prof):
        logger.warning(f"User {username} denied access to view students for subject {subject_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not a professor or regent for this subject."
        )

    # 3. Fetch from Keycloak
    students_data = await keycloak_client.get_subject_students(str(subject_id))
    
    # 4. Map to DTO
    return [
        StudentInfo(
            id=s['id'], 
            username=s['username'], 
            email=s.get('email'),
            first_name=s.get('firstName'),
            last_name=s.get('lastName')
        ) 
        for s in students_data
    ]


@router.post("/{subject_id}/students", status_code=status.HTTP_201_CREATED)
async def add_students_to_subject(
    subject_id: int,
    request: StudentAddRequest,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Add students to a subject.
    Access: Manager OR Subject Regent OR User in 'add_students' group.
    """
    # 1. Check if Subject exists
    subject = await session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # 2. Permission Check
    username = user_info.get("username")
    user_groups = user_info.get("groups", [])
    user_roles = user_info.get("realm_roles", [])

    regent_group = f"s{subject_id}/regent"
    add_student_group = f"s{subject_id}/add_students"

    is_manager = "manager" in user_roles
    is_regent = any(g.endswith(regent_group) for g in user_groups)
    can_add = any(g.endswith(add_student_group) for g in user_groups)

    if not (is_manager or is_regent or can_add):
        logger.warning(f"User {username} denied access to add students to subject {subject_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to add students to this subject."
        )

    # 3. Add to Keycloak Group
    try:
        await keycloak_client.add_students_to_subject(
            subject_id=str(subject_id), 
            student_ids=request.student_keycloak_ids
        )
        return {"message": "Students added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add students to Keycloak group")
    


async def verify_manager_or_regent(subject_id: int, user_info: dict):
    """Helper to enforce Manager or Regent access"""
    username = user_info.get("username")
    roles = user_info.get("realm_roles", [])
    groups = user_info.get("groups", [])
    
    is_manager = "manager" in roles
    is_regent = any(g.endswith(f"s{subject_id}/regent") for g in groups)
    
    if not (is_manager or is_regent):
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Managers or the Subject Regent can manage professors."
        )

@router.post("/{subject_id}/professors", status_code=status.HTTP_201_CREATED)
async def add_professor_to_subject(
    subject_id: int,
    request: ProfessorAddRequest,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Add a professor to the subject and set their specific permissions.
    """
    # 1. Existence and Permission Checks
    subject = await session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    await verify_manager_or_regent(subject_id, user_info)

    # 2. Verify the user being added exists
    await verify_regent_exists(request.professor_keycloak_id) # We can reuse this validator

    # 3. Convert Pydantic model to dict (excluding the ID)
    permissions_dict = request.model_dump(exclude={"professor_keycloak_id"})

    # 4. Sync with Keycloak
    try:
        await keycloak_client.manage_professor_permissions(
            subject_id=str(subject_id),
            professor_id=request.professor_keycloak_id,
            permissions=permissions_dict
        )
        return {"message": "Professor added and permissions set successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update Keycloak groups.")

@router.put("/{subject_id}/professors/{professor_id}")
async def update_professor_permissions(
    subject_id: int,
    professor_id: str,
    request: ProfessorUpdateRequest,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Update permissions for an existing professor on this subject.
    """
    subject = await session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    await verify_manager_or_regent(subject_id, user_info)

    # Convert permissions to dict
    permissions_dict = request.model_dump()

    try:
        await keycloak_client.manage_professor_permissions(
            subject_id=str(subject_id),
            professor_id=professor_id,
            permissions=permissions_dict
        )
        return {"message": "Professor permissions updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update Keycloak groups.")

@router.delete("/{subject_id}/professors/{professor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_professor_from_subject(
    subject_id: int,
    professor_id: str,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Remove a professor from the subject entirely (removes from all subject groups).
    """
    subject = await session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    await verify_manager_or_regent(subject_id, user_info)

    success = await keycloak_client.remove_professor_from_subject(
        subject_id=str(subject_id),
        professor_id=professor_id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove professor from Keycloak groups.")
    
    return None