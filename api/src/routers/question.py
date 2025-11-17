from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from src.core.db import get_session
from src.models.question import QuestionCreate, QuestionUpdate, QuestionRead
from src.services.question import create_question, get_questions_by_subject, update_question,delete_question


router = APIRouter()


@router.post("/", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
async def api_create_question(
    data: QuestionCreate,
    session: AsyncSession = Depends(get_session)
):
    return await create_question(session, data)


@router.get("/", response_model=List[QuestionRead])
async def api_get_questions(
    subject_id: int ,
    session: AsyncSession = Depends(get_session)
):
    return await get_questions_by_subject(session, subject_id)


@router.put("/{id}", response_model=QuestionRead)
async def api_update_question(
    id: int,
    data: QuestionUpdate,
    session: AsyncSession = Depends(get_session)
):
    result = await update_question(session, id, data)

    if not result:
        raise HTTPException(status_code=404, detail="Question not found")

    return result

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_question(
    id: int,
    session: AsyncSession = Depends(get_session)
):
    deleted = await delete_question(session, id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Question not found")

    return None  # FastAPI will return an empty 204 response
