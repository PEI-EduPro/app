from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.db import get_session

from src.models.question_option import QuestionOptionCreate,QuestionOptionRead


from src.services.question_option import create_question_options,delete_question_option

router = APIRouter()


@router.post("/{question_id}/options", response_model=List[QuestionOptionRead])
async def api_create_options(
    question_id: int,
    options: List[QuestionOptionCreate],
    session: AsyncSession = Depends(get_session)
):
    """Create one or multiple options for a question."""
    return await create_question_options(session, question_id, options)


@router.delete("/{question_id}/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_option(
    question_id: int,
    option_id: int,
    session: AsyncSession = Depends(get_session)
):
    deleted = await delete_question_option(session, question_id, option_id)

    if not deleted:
        raise HTTPException(
            status_code=404, 
            detail="Option not found"
        )

    return None
