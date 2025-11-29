from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from api.src.core.db import get_session
from api.src.core.deps import get_current_user_info, require_subject_regent, verify_regent_exists
from api.src.models.question import Question, QuestionCreate, QuestionRead, QuestionUpdate
from api.src.models.user import User
from sqlmodel.ext.asyncio.session import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/question/{subject}/{topic}", response_model=QuestionRead, dependencies=[Depends(require_subject_regent)])
async def create_question(
    subject_name: str,
    topic_name: str,
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user_info), # This will be the regent's info due to verify_regent_exists
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new question (regent only).
    Requires the 'regent' role.
    """
    logger.info(f"Regent {current_user.user_id} is attempting to create a new question: {question_data.question_text} in subject {subject_name} in topic {topic_name}")

    try:
        # 1. Verify current_user is regent BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have current_user
        regent_info = await verify_regent_exists(current_user.user_id)

        # 2. Create the Topic in the local database
        db_question = Question(topic_id=question_data.topic_id,question_text=question_data.question_text)
        session.add(db_question)
        await session.commit()
        await session.refresh(db_question) # Get the auto-generated ID

        logger.info(f"Question '{db_question.question_text}' created in successfully with ID: {db_question.id}")

        # Return success response
        return QuestionRead.model_validate(db_question)
        
    except ValueError as ve:
        # Handle specific validation errors like user exists
        logger.warning(f"Failed to create question {question_data.question_text}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation
        logger.error(f"Failed to create user {question_data.question_text} by regent {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user in Keycloak."
        )
    
    
@router.get("/question/{id}", response_model=QuestionRead)
async def get_question(
    id: int,
    session: AsyncSession = Depends(get_session)
    # session: AsyncSession = Depends(get_session) # Remove this dependency
):
    """Get topic info from provided id"""
    result = await session.get(Question, id)
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionRead.model_validate(result)


@router.put("/question/{id}", response_model=QuestionRead)
async def put_question(
    id: int,
    question_data: QuestionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_info), # This will be the regent's info due to verify_regent_exists
    # session: AsyncSession = Depends(get_session) # Remove this dependency
):
    """Update question info from provided id"""
    try:
        # 1. Verify current_user is regent BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have current_user
        regent_info = await verify_regent_exists(current_user.user_id)


        statement = select(Question).where(Question.id == id)
        results = await session.exec(statement)
        question = results.one()

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question.question_text = question_data.question_text
        question.topic_id = question_data.question_text
        session.add(question)
        session.commit()
        session.refresh(question)

        return QuestionRead.model_validate(question)
        
        
    except ValueError as ve:
        # Handle specific validation errors like user exists
        logger.warning(f"Failed to create question {question_data.question_text}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation
        logger.error(f"Failed to create user {question_data.question_text} by regent {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user in Keycloak."
        )


@router.delete("/question/{id}", response_model=str)
async def put_question(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_info), # This will be the regent's info due to verify_regent_exists
    # session: AsyncSession = Depends(get_session) # Remove this dependency
):
    """Delete question from provided id"""
    try:
        # 1. Verify current_user is regent BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have current_user
        regent_info = await verify_regent_exists(current_user.user_id)


        statement = select(Question).where(Question.id == id)
        results = await session.exec(statement)
        question = results.one()

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        session.delete(question)
        session.commit()

        statement = select(Question).where(Question.id == id)
        results = await session.exec(statement)
        question = results.first()

        if question is None:
            return "Question deleted successfully"
        else:
            raise ValueError("question is not None")
        
        
    except ValueError as ve:
        # Handle specific validation errors like user exists
        logger.warning(f"Failed to delete question: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation
        logger.error(f"Failed to delete question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the question."
        )