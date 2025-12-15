from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlmodel import select
from src.models.question_option import QuestionOptionPublic
from src.services import question
from src.core.db import get_session
from src.core.deps import get_current_user_info, require_subject_regent, verify_regent_exists
from src.models.question import Question, QuestionCreate, QuestionPublic, QuestionUpdate
from src.models.user import User
from sqlmodel.ext.asyncio.session import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=List[QuestionPublic])#, dependencies=[Depends(require_subject_regent)])
async def create_question(
    question_data: List[QuestionCreate],
    #current_user: User = Depends(get_current_user_info), # This will be the regent's info due to verify_regent_exists
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new question (regent only).
    Requires the 'regent' role.
    """
    #logger.info(f"Regent {current_user.user_id} is attempting to create a new question: {question_data.question_text}")

    try:
        # 1. Verify current_user is regent BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have current_user
        #regent_info = await verify_regent_exists(current_user.user_id)

        # 2. Create the Topic in the local database
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
    

@router.post("/{subject_id}/XML", response_model=dict)#, dependencies=[Depends(require_subject_regent)])
async def create_question_from_XML(
    subject_id: int,
    xml: str = Body(required=True,media_type="application/xml"),
    #current_user: User = Depends(get_current_user_info), # This will be the regent's info due to verify_regent_exists
    session: AsyncSession = Depends(get_session)
):
    "Create questions from XML file"
    result = await question.create_question_XML(session,subject_id,xml)

    return result
    
    
@router.get("/{id}", response_model=QuestionPublic)
async def get_question(
    id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get question info from provided id"""
    result = await question.get_question_by_id(session,id)

    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return result

@router.get("/{id}/question-options", response_model=List[QuestionOptionPublic])
async def get_question_options(
    id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get question options info from provided question id"""
    result = await question.get_question_options_by_question_id(session,id)

    if not result:
        raise HTTPException(status_code=404, detail="Question options not found")
    
    return result


@router.put("/{id}", response_model=QuestionPublic)
async def put_question(
    id: int,
    question_data: QuestionUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update question info from provided id"""
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
    session: AsyncSession = Depends(get_session),
):
    """Delete question from provided id"""
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