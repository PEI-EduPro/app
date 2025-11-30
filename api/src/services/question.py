from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.question import Question, QuestionCreate, QuestionPublic, QuestionUpdate
from typing import Optional, List


async def create_question(
    session: AsyncSession,
    question_data: QuestionCreate
) -> QuestionPublic:
    """Create a new question"""
    question = Question.model_validate(question_data)
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return QuestionPublic.model_validate(question)


async def get_question_by_id(session: AsyncSession, question_id: int) -> Optional[QuestionPublic]:
    """Get a question by its ID"""
    statement = select(Question).where(Question.id == question_id)
    result = await session.exec(statement)
    result = result.one_or_none()
    return QuestionPublic.model_validate(result)


async def update_question(
    session: AsyncSession,
    question_data: QuestionUpdate
) -> Optional[QuestionPublic]:
    """Update a question"""
    statement = select(Question).where(Question.id == question_data.id)
    question = await session.exec(statement)
    question = question.one_or_none()

    if not question:
            raise HTTPException(status_code=404, detail="Question not found")
    
    question.sqlmodel_update(question_data)
    
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return QuestionPublic.model_validate(question)


async def delete_question(session: AsyncSession, question_id: int) -> bool:
    """Delete a question by ID"""
    statement = select(Question).where(Question.id == question_id)
    question = await session.exec(statement)
    question = question.one_or_none()
    
    if not question:
        return False
    
    await session.delete(question)
    await session.commit()
    return True