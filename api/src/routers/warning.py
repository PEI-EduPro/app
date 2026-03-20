from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from src.core.db import get_session
from src.models.user import User
from src.models.exam_config import ExamConfig
from src.models.warning import ExamWarningResponse
from src.core.deps import get_current_user_info, verify_permission
from src.services.warning import get_warnings_by_exam_config_id

router = APIRouter()

@router.get("/exam_config/{exam_config_id}", response_model=List[ExamWarningResponse])
async def get_exam_config_warnings(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all warnings associated with an exam configuration.
    Only the regent of the subject can perform this action.
    """
    exam_config = await session.get(ExamConfig, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")
        
    # Verify permission - only regent can view warnings for this subject
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])
    
    try:
        warnings = await get_warnings_by_exam_config_id(session, exam_config_id)
        return warnings
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to fetch warnings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
