from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from src.core.db import get_session
from src.models.user import User
from src.models.exam_config import ExamConfig
from src.models.waiting_room import WaitingRoom
from src.models.warning import ExamWarningResponse, ResolveWarningsRequest, WarningsWithStudentsResponse
from src.core.deps import get_current_user_info, verify_permission
from src.services.warning import get_warnings_by_waiting_room_id, resolve_warnings_service, get_filtered_students

router = APIRouter()


@router.get("/{waiting_room_id}", response_model=WarningsWithStudentsResponse)
async def get_waiting_room_warnings(
    waiting_room_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all warnings and filtered student list for a waiting room.
    Students returned are those with no association OR are involved in any warning.
    Only the regent of the subject can perform this action.
    """
    waiting_room = await session.get(WaitingRoom, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=404, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    # Verify permission - only regent can view warnings for this subject
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    try:
        warnings = await get_warnings_by_waiting_room_id(session, waiting_room_id)
        students = await get_filtered_students(session, waiting_room_id)
        return WarningsWithStudentsResponse(warnings=warnings, students=students)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to fetch warnings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{waiting_room_id}/resolve", response_model=List[ExamWarningResponse])
async def resolve_waiting_room_warnings(
    waiting_room_id: int,
    body: ResolveWarningsRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Resolve warnings by providing a batch of exam->student assignments.
    Each assignment overwrites the current nmec on that exam.
    Old warnings are cleared and recalculated from the updated state.
    Only the regent of the subject can perform this action.

    Request body:
    {
        "assignments": [
            {"exam_id": 1, "student_nmec": "12345"},
            {"exam_id": 2, "student_nmec": "67890"}
        ]
    }
    """
    waiting_room = await session.get(WaitingRoom, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=404, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    try:
        return await resolve_warnings_service(session, waiting_room_id, body.assignments)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to resolve warnings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
