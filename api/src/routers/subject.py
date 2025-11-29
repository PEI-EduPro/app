# src/routers/subject.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

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

# --- Helpers ---
async def verify_manager_or_regent(subject_id: int, user_info: dict):
    username = user_info.username
    roles = user_info.realm_roles
    groups = user_info.groups
    
    is_manager = "manager" in roles
    is_regent = any(g.endswith(f"s{subject_id}/regent") for g in groups)
    
    if not (is_manager or is_regent):
         logger.warning(f"User {username} denied access (Not Manager/Regent)")
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Managers or the Subject Regent can perform this action."
        )

# --- Endpoints ---

@router.post("/", response_model=SubjectCreateResponse, dependencies=[Depends(require_manager)])
async def create_subject_endpoint(
    subject_data: SubjectCreateRequest,
    session: AsyncSession = Depends(get_session)
):
    try:
        result = await subject_service.create_subject_service(
            session=session,
            name=subject_data.name,
            regent_keycloak_id=subject_data.regent_keycloak_id
        )
        return SubjectCreateResponse(
            id=result["subject"].id,
            name=result["subject"].name,
            message="Subject and Keycloak groups created successfully.",
            regent_username=result["regent_username"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating subject: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/", response_model=List[SubjectRead])
async def get_subjects(
    session: AsyncSession = Depends(get_session),
    user_info: dict = Depends(get_current_user_info)
):
    return await subject_service.get_subjects_for_user(session, user_info)

@router.put("/{subject_id}", response_model=SubjectRead, dependencies=[Depends(require_manager)])
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await subject_service.update_subject_service(session, subject_id, subject_update)
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_subject(
    subject_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await subject_service.delete_subject_service(session, subject_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")

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

    try:
        students = await subject_service.get_students_service(session, subject_id)
        return [
            StudentInfo(
                id=s['id'], 
                username=s['username'], 
                email=s.get('email'), 
                first_name=s.get('firstName'), 
                last_name=s.get('lastName')
            ) for s in students
        ]
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")

@router.post("/{subject_id}/students", status_code=status.HTTP_201_CREATED)
async def add_students_to_subject(
    subject_id: int,
    request: StudentAddRequest,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    # Permission Check
    roles = user_info.realm_roles
    groups = user_info.groups
    if not ("manager" in roles or 
            any(g.endswith(f"s{subject_id}/regent") for g in groups) or 
            any(g.endswith(f"s{subject_id}/add_students") for g in groups)):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        await subject_service.add_students_service(session, subject_id, request.student_keycloak_ids)
        return {"message": "Students added successfully"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add students")

@router.post("/{subject_id}/professors", status_code=status.HTTP_201_CREATED)
async def add_professor_to_subject(
    subject_id: int,
    request: ProfessorAddRequest,
    user_info: dict = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    await verify_manager_or_regent(subject_id, user_info)
    try:
        await subject_service.manage_professor_service(
            session, 
            subject_id, 
            request.professor_keycloak_id, 
            request.model_dump(exclude={"professor_keycloak_id"}),
            is_update=False
        )
        return {"message": "Professor added successfully."}
    except ValueError as e:
        # Catch "Subject not found" or "Regent not found"
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

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