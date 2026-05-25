import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.db import get_session
from src.core.deps import get_current_user_info, verify_permission
from src.models.exam_config import ExamConfig
from src.models.user import User
from src.models.warning import ExamWarningResponse, ResolveWarningsRequest, WarningsWithStudentsResponse
from src.services.warning import get_warnings_by_exam_config_id, resolve_warnings_service, get_filtered_students

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{exam_config_id}", response_model=WarningsWithStudentsResponse)
async def get_exam_config_warnings(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all warnings and filtered student list for an exam configuration.
    Students returned are those with no association OR are involved in any warning.
    Only the regent of the subject can perform this action.
    """
    exam_config = await session.get(ExamConfig, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    # Verify permission - only regent can view warnings for this subject
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    try:
        warnings = await get_warnings_by_exam_config_id(session, exam_config_id)
        students = await get_filtered_students(session, exam_config_id)
        return WarningsWithStudentsResponse(warnings=warnings, students=students)
    except Exception as e:
        logger.error(f"Failed to fetch warnings for exam config {exam_config_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch warnings")


@router.post("/{exam_config_id}/resolve", response_model=List[ExamWarningResponse])
async def resolve_exam_config_warnings(
    exam_config_id: int,
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
    exam_config = await session.get(ExamConfig, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    try:
        return await resolve_warnings_service(session, exam_config_id, body.assignments)
    except Exception as e:
        logger.error(f"Failed to resolve warnings for exam config {exam_config_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resolve warnings")
