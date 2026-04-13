from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.db import get_session
from src.core.deps import require_manager, get_current_user_info, verify_permission
from src.models.user import User 
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
from src.models.common import MessageResponse
from src.models.topic import TopicPublic
import src.services.subject as subject_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Endpoints ---

@router.post("/", response_model=SubjectCreateResponse, dependencies=[Depends(require_manager)])
async def create_subject_endpoint(
    subject_data: SubjectCreateRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new subject. Delegates complex logic (DB + Keycloak) to the service layer.
    """
    try:
        result = await subject_service.create_subject_service(
            session=session,
            name=subject_data.name,
            regent_keycloak_id=subject_data.regent_keycloak_id,
            student_keycloak_ids=subject_data.student_keycloak_ids,
            professor_keycloak_ids=subject_data.professor_keycloak_ids
        )
        return SubjectCreateResponse(
            id=result["subject"].id,
            name=result["subject"].name,
            message="Subject and Keycloak groups created successfully.",
            regent_username=result["regent_username"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating subject: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/", response_model=List[SubjectRead])
async def get_subjects(
    session: AsyncSession = Depends(get_session),
    user_info: User = Depends(get_current_user_info)
):
    """
    Get subjects the user has access to.
    """
    return await subject_service.get_subjects_for_user(session, user_info)

@router.get("/{subject_id}", response_model=SubjectRead)
async def get_subject(subject_id: int, session: AsyncSession = Depends(get_session)):
    """Get subject by ID."""
    subject = await subject_service.get_subject_by_id(session, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@router.put("/{subject_id}", response_model=SubjectRead)
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Update subject.
    - Managers: Can update name, regent, students, and professors.
    - Regents: Can only update students and professors for their subject.
    """
    # Check if user is manager or regent of this subject
    is_manager = "manager" in user_info.realm_roles
    is_regent = f"/s{subject_id}/regent" in user_info.groups
    
    if not is_manager and not is_regent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers or subject regents can update subjects"
        )
    
    # Regents can only update students and professors, not name or regent
    if not is_manager:
        current = await subject_service.get_subject_by_id(session, subject_id)
        if not current:
            raise HTTPException(status_code=404, detail="Subject not found")
        name_changed = subject_update.name is not None and subject_update.name != current.name
        regent_changed = False
        if subject_update.regent_keycloak_id is not None:
            try:
                current_regent = await subject_service.get_regent_service(session, subject_id)
                regent_changed = subject_update.regent_keycloak_id != current_regent.get("id")
            except ValueError:
                regent_changed = True
        if name_changed or regent_changed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can update subject name or regent"
            )
    
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
    """
    Delete subject and clean up Keycloak groups.
    """
    try:
        await subject_service.delete_subject_service(session, subject_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except Exception as e:
        logger.error(f"Error deleting subject: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete subject")

# --- Keycloak Management Endpoints ---

@router.get("/{subject_id}/students", response_model=List[StudentInfo])
async def get_subject_students(
    subject_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    View enrolled students.
    """
    verify_permission(user_info, [f"/s{subject_id}/professors", f"/s{subject_id}/regent"], allow_manager=True)
    try:
        students = await subject_service.get_students_service(session, subject_id)
        # Map raw dictionary from Keycloak to Pydantic model
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

@router.get("/{subject_id}/professors", response_model=List[StudentInfo])
async def get_subject_professors(
    subject_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """View professors in subject"""
    verify_permission(user_info, [f"/s{subject_id}/professors", f"/s{subject_id}/regent"], allow_manager=True)
    try:
        professors = await subject_service.get_professors_service(session, subject_id)
        return [
            StudentInfo(
                id=p['id'], 
                username=p['username'], 
                email=p.get('email'), 
                first_name=p.get('firstName'), 
                last_name=p.get('lastName')
            ) for p in professors
        ]
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")

@router.get("/{subject_id}/regent", response_model=StudentInfo)
async def get_subject_regent(
    subject_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """View subject regent"""
    verify_permission(user_info, [f"/s{subject_id}", f"/s{subject_id}/regent"], allow_manager=True)
    try:
        regent = await subject_service.get_regent_service(session, subject_id)
        return StudentInfo(
            id=regent['id'], 
            username=regent['username'], 
            email=regent.get('email'), 
            first_name=regent.get('firstName'), 
            last_name=regent.get('lastName')
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found or no regent assigned")

@router.post("/{subject_id}/students", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def add_students_to_subject(
    subject_id: int,
    request: StudentAddRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Add students to a subject.
    """
    verify_permission(user_info, [f"/s{subject_id}/add_students", f"/s{subject_id}/regent"], allow_manager=True)
    try:
        await subject_service.add_students_service(session, subject_id, request.student_keycloak_ids)
        return {"message": "Students added successfully"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add students")

@router.post("/{subject_id}/professors", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def add_professor_to_subject(
    subject_id: int,
    request: ProfessorAddRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Add a professor with specific permissions.
    """
    verify_permission(user_info, [f"/s{subject_id}/regent"], allow_manager=True)
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/{subject_id}/professors/{professor_id}", response_model=MessageResponse)
async def update_professor_permissions(
    subject_id: int,
    professor_id: str,
    request: ProfessorUpdateRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Update permissions for an existing professor.
    """
    verify_permission(user_info, [f"/s{subject_id}/regent"], allow_manager=True)
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
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Remove a professor from all subject groups.
    """
    verify_permission(user_info, [f"/s{subject_id}/regent"], allow_manager=True)
    try:
        await subject_service.remove_professor_service(session, subject_id, professor_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except RuntimeError:
        raise HTTPException(status_code=500, detail="Failed to remove professor")

# --- Existing Endpoints (Kept from current version) ---

@router.get("/{subject_id}/topics", response_model=List[Tuple[TopicPublic, int]])
async def get_all_topics_by_subject(
    subject_id: int, 
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Get all subject topics by subject ID."""
    verify_permission(user_info, [f"/s{subject_id}/view_question_bank", f"/s{subject_id}/regent"])
    result = await subject_service.get_all_subject_topics(session, subject_id)
    if not result:
        raise HTTPException(status_code=404, detail="Topics not found")
    return result


@router.get("/{subject_id}/all-questions", response_model=dict)
async def get_all_by_subject(
    subject_id: int, 
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Get subject by ID."""
    verify_permission(user_info, [f"/s{subject_id}/view_question_bank", f"/s{subject_id}/regent"])
    result = await subject_service.get_topics_questions_and_options_by_subject_id(session, subject_id)
    if not result:
        raise HTTPException(status_code=404, detail="Subject not found")
    return result

# Note: get_subject_topics in the previous file seemed redundant with get_all_topics_by_subject, 
# but checking the return type (List[TopicPublic] vs List[Tuple[TopicPublic, int]]), I will keep it
# but rename it slightly or keep it as is if it was used differently.
# The original file had both. I'll keep the one that matches the signature found in the previous read.

@router.get("/{subject_id}/topics-list", response_model=List[TopicPublic])
async def get_subject_topics_list(
    subject_id: int, 
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Get all topics from a given subject_id (Simple List)"""
    verify_permission(user_info, [f"/s{subject_id}/view_question_bank", f"/s{subject_id}/regent"])
    return await subject_service.get_topics_from_subject(session, subject_id)
