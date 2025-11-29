from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from src.models.question_option import QuestionOption, QuestionOptionCreate, QuestionOptionPublic
from src.core.db import get_session
from src.core.deps import get_current_user_info, require_subject_regent, verify_regent_exists
from src.models.user import User
from sqlmodel.ext.asyncio.session import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=QuestionOptionPublic)
async def create_question_option(
    question_option_data: QuestionOptionCreate,  # Fixed variable name
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new question option.
    """
    try:
        # Create the QuestionOption in the local database
        db_question_option = QuestionOption.model_validate(question_option_data)  # Fixed variable name
        session.add(db_question_option)
        await session.commit()
        await session.refresh(db_question_option)  # Get the auto-generated ID

        logger.info(f"Question option '{db_question_option.option_text}' created successfully with ID: {db_question_option.id}")  # Fixed logging

        # Return success response
        return QuestionOptionPublic.model_validate(db_question_option)
        
    except ValueError as ve:
        # Handle specific validation errors
        logger.warning(f"Failed to create question option {question_option_data.option_text}: {ve}")  # Fixed logging
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation
        logger.error(f"Failed to create question option: {e}")  # Fixed logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the question option."
        )