import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.db import get_session
from src.core.deps import get_current_user_info, verify_permission
from src.models.common import MessageResponse
from src.models.question_option import QuestionOption, QuestionOptionCreate, QuestionOptionPublic, QuestionOptionUpdate
from src.models.user import User
from src.services import question_option
from src.services import question as question_service
from src.services import topic as topic_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=List[QuestionOptionPublic])
async def create_question_options(
    question_options_data: List[QuestionOptionCreate],
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Create multiple question options"""
    try:
        if not question_options_data:
            raise ValueError("No question options provided.")
            
        first_question_id = question_options_data[0].question_id
        q = await question_service.get_question_by_id(session, first_question_id)
        if not q:
            raise ValueError(f"Question {first_question_id} not found.")
            
        topic = await topic_service.get_topic_by_id(session, q.topic_id)
        if not topic:
            raise ValueError(f"Topic {q.topic_id} not found.")
            
        verify_permission(user_info, [f"/s{topic.subject_id}/edit_questions", f"/s{topic.subject_id}/regent"])
        
        db_options = await question_option.create_question_options(session, question_options_data)
        return db_options
    except ValueError as ve:
        logger.warning(f"Failed to create question options: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create question options: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating question options.")

@router.put("/{id}", response_model=QuestionOptionPublic)
async def update_question_option(
    id: int,
    option_data: QuestionOptionUpdate,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Update a question option"""
    existing_option = await session.get(QuestionOption, id)
    if not existing_option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question option not found.")
        
    q = await question_service.get_question_by_id(session, existing_option.question_id)
    topic = await topic_service.get_topic_by_id(session, q.topic_id)
    verify_permission(user_info, [f"/s{topic.subject_id}/edit_questions", f"/s{topic.subject_id}/regent"])
    
    try:
        result = await question_option.update_question_option(session, id, option_data)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question option not found.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update question option: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while updating the question option.")

@router.delete("/{id}", response_model=MessageResponse)
async def delete_question_option(
    id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Delete a question option"""
    existing_option = await session.get(QuestionOption, id)
    if not existing_option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question option not found.")
        
    q = await question_service.get_question_by_id(session, existing_option.question_id)
    topic = await topic_service.get_topic_by_id(session, q.topic_id)
    verify_permission(user_info, [f"/s{topic.subject_id}/edit_questions", f"/s{topic.subject_id}/regent"])
    try:
        if await question_option.delete_question_option(session, id):
            return {"message": "Question option deleted successfully"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question option not found.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete question option: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while deleting the question option.")