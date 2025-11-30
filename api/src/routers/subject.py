# src/routers/subject.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.subject import Subject, SubjectCreate, SubjectPublic
from src.core.db import get_session
from src.core.deps import require_manager, get_current_user_info
from src.models.subject import (
    SubjectCreateRequest, 
    SubjectCreateResponse, 
    SubjectRead,
    SubjectUpdate,
    StudentAddRequest,
    StudentInfo,
    ProfessorAddRequest,
    ProfessorUpdateRequest
)
# Import the new service functions
import src.services.subject as subject_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=SubjectPublic)#, dependencies=[Depends(require_manager)])
async def create_subject_endpoint(
    subject_data: SubjectCreate, # Receive the request body data
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new subject in the database and its corresponding Keycloak groups.
    Assigns the specified user as the regent.
    Requires the 'manager' role.
    """
    #logger.info(f"Manager is attempting to create a new subject: '{subject_data.name}', assigning regent ID: {subject_data.regent_keycloak_id}")

@router.put("/{subject_id}", response_model=SubjectRead, dependencies=[Depends(require_manager)])
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        # 1. Verify regent exists BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have subject_data
        #regent_info = await verify_regent_exists(subject_data.regent_keycloak_id)

        # 2. Create the Subject in the local database
        db_subject = Subject.model_validate(subject_data)
        session.add(db_subject)
        await session.commit()
        await session.refresh(db_subject) # Get the auto-generated ID

@router.get("/{subject_id}/students", response_model=List[StudentInfo])
async def get_subject_students(
    subject_id: int,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    # Permission Check (kept in router as it relies on HTTP Context)
    roles = user_info.realm_roles
    groups = user_info.groups
    if not ("manager" in roles or 
            any(g.endswith(f"s{subject_id}/regent") for g in groups) or 
            any(g.endswith(f"s{subject_id}/professors") for g in groups)):
        raise HTTPException(status_code=403, detail="Access denied")

        # 3. Create Keycloak groups and assign regent using the ID from the database
        #success = await keycloak_client.create_subject_groups_and_assign_regent(
        #    subject_id=str(db_subject.id), # Use the DB ID to name the groups
        #    regent_keycloak_id=subject_data.regent_keycloak_id
        #)

        # if not success:
        #     # If group creation/assignment failed, consider rolling back the DB creation
        #     # For now, just log and raise an error
        #     logger.error(f"Failed to create Keycloak groups for subject {db_subject.id}. DB entry may need cleanup.")
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail="Subject created in database, but failed to create Keycloak groups."
        #     )

    try:
        await subject_service.add_students_service(session, subject_id, request.student_keycloak_ids)
        return {"message": "Students added successfully"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add students")

        # Return success response
        return SubjectPublic.model_validate(db_subject)

@router.put("/{subject_id}/professors/{professor_id}")
async def update_professor_permissions(
    subject_id: int,
    professor_id: str,
    request: ProfessorUpdateRequest,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    await verify_manager_or_regent(subject_id, user_info)
    try:
        await subject_service.manage_professor_service(
            session, 
            subject_id, 
            professor_id, 
            request.model_dump(),
            is_update=True
        )
        return {"message": "Permissions updated successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/{subject_id}/professors/{professor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_professor_from_subject(
    subject_id: int,
    professor_id: str,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    await verify_manager_or_regent(subject_id, user_info)
    try:
        await subject_service.remove_professor_service(session, subject_id, professor_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except RuntimeError:
        raise HTTPException(status_code=500, detail="Failed to remove professor")