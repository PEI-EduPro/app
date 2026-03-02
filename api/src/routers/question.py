from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlmodel import select
from src.models.question_option import QuestionOptionPublic
from src.services import question
from src.services import topic as topic_service
from src.core.db import get_session
from src.core.deps import get_current_user_info, verify_permission
from src.models.question import Question, QuestionCreate, QuestionPublic, QuestionUpdate
from src.models.user import User
from sqlmodel.ext.asyncio.session import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=List[QuestionPublic])
async def create_question(
    question_data: List[QuestionCreate],
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new question (regent only).
    Requires the 'edit_questions' group permission.
    """
    try:
        # Get the topic to know the subject
        if not question_data:
            raise ValueError("No questions provided.")
            
        first_topic_id = question_data[0].topic_id
        topic = await topic_service.get_topic_by_id(session, first_topic_id)
        if not topic:
            raise ValueError(f"Topic {first_topic_id} not found.")
            
        # Verify permission
        verify_permission(user_info, [f"/s{topic.subject_id}/edit_questions", f"/s{topic.subject_id}/regent"])

        # 2. Create the Question in the local database
        db_questions = await question.create_question(session,question_data)

        question_ids = [q.id for q in db_questions]
        logger.info(f"Created {len(db_questions)} questions successfully with IDs: {question_ids}")

        # Return success response
        return db_questions
        
    except ValueError as ve:
        # Handle specific validation errors like user exists
        logger.warning(f"Failed to create questions : {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to create questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while creating the question."
        )
    

@router.post("/{subject_id}/XML", response_model=dict)
async def create_question_from_XML(
    subject_id: int,
    xml: str = Body(required=True,media_type="application/xml"),
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    "Create questions from XML file"
    verify_permission(user_info, [f"/s{subject_id}/edit_questions", f"/s{subject_id}/regent"])
    result = await question.create_question_XML(session,subject_id,xml)

    return result
    
    
@router.get("/{id}", response_model=QuestionPublic)
async def get_question(
    id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Get question info from provided id"""
    result = await question.get_question_by_id(session,id)

    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
        
    topic = await topic_service.get_topic_by_id(session, result.topic_id)
    verify_permission(user_info, [f"/s{topic.subject_id}/view_question_bank", f"/s{topic.subject_id}/regent"])
    
    return result

@router.get("/{id}/question-options", response_model=List[QuestionOptionPublic])
async def get_question_options(
    id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Get question options info from provided question id"""
    q_result = await question.get_question_by_id(session,id)
    if not q_result:
        raise HTTPException(status_code=404, detail="Question not found")
        
    topic = await topic_service.get_topic_by_id(session, q_result.topic_id)
    verify_permission(user_info, [f"/s{topic.subject_id}/view_question_bank", f"/s{topic.subject_id}/regent"])
        
    result = await question.get_question_options_by_question_id(session,id)

    if not result:
        raise HTTPException(status_code=404, detail="Question options not found")
    
    return result


@router.put("/{id}", response_model=QuestionPublic)
async def put_question(
    id: int,
    question_data: QuestionUpdate,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session),
):
    """Update question info from provided id"""
    q_result = await question.get_question_by_id(session,id)
    if not q_result:
        raise HTTPException(status_code=404, detail="Question not found")
        
    topic = await topic_service.get_topic_by_id(session, q_result.topic_id)
    verify_permission(user_info, [f"/s{topic.subject_id}/edit_questions", f"/s{topic.subject_id}/regent"])
    try:
        result = await question.update_question(session, question_data)
        return result
    except ValueError as ve:
        logger.warning(f"Failed to update question: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to update question: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while updating the question.")


@router.delete("/{id}", response_model=str)
async def delete_question(
    id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session),
):
    """Delete question from provided id"""
    q_result = await question.get_question_by_id(session,id)
    if not q_result:
        raise HTTPException(status_code=404, detail="Question not found")
        
    topic = await topic_service.get_topic_by_id(session, q_result.topic_id)
    verify_permission(user_info, [f"/s{topic.subject_id}/edit_questions", f"/s{topic.subject_id}/regent"])
    try:
        result = await question.delete_question(session, id)
        if result:
            return "Question deleted successfully"
        raise ValueError("Question not found")
    except ValueError as ve:
        logger.warning(f"Failed to delete question: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to delete question: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while deleting the question.")