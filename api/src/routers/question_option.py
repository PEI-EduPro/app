from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from src.services import question_option
from src.models.question_option import QuestionOption, QuestionOptionCreate, QuestionOptionPublic, QuestionOptionUpdate
from src.core.db import get_session
from src.core.deps import get_current_user_info, require_subject_regent, verify_regent_exists
from src.models.user import User
from sqlmodel.ext.asyncio.session import AsyncSession
import logging
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=List[QuestionOptionPublic])
async def create_question_options(
    question_options_data: List[QuestionOptionCreate],
    session: AsyncSession = Depends(get_session)
):
    """Create multiple question options"""
    try:
        db_options = await question_option.create_question_options(session, question_options_data)
        return db_options
    except ValueError as ve:
        logger.warning(f"Failed to create question options: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to create question options: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating question options.")

@router.put("/{id}", response_model=QuestionOptionPublic)
async def update_question_option(
    id: int,
    option_data: QuestionOptionUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a question option"""
    try:
        result = await question_option.update_question_option(session, id, option_data)
        if not result:
            raise HTTPException(status_code=404, detail="Question option not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update question option: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while updating the question option.")

@router.delete("/{id}")
async def delete_question_option(
    id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a question option"""
    try:
        if await question_option.delete_question_option(session, id):
            return {"message": "Question option deleted successfully"}
        raise HTTPException(status_code=404, detail="Question option not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete question option: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while deleting the question option.")