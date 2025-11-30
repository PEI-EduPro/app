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
    question = Question(question_data)
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return QuestionPublic.model_validate(question)


async def get_question_by_id(session: AsyncSession, question_id: int) -> Optional[QuestionPublic]:
    """Get a question by its ID"""
    statement = select(Question).where(Question.id == question_id)
    result = await session.exec(statement).first()
    return QuestionPublic.model_validate(result)


async def update_question(
    session: AsyncSession,
    question_data: QuestionUpdate
) -> Optional[QuestionPublic]:
    """Update a question"""
    statement = select(Question).where(Question.id == question_data.id)
    question = await session.exec(statement).first()

    if not question:
            raise HTTPException(status_code=404, detail="Question not found")
    
    # Update fields
    for key, value in question_data.items():
        if hasattr(question, key) and value is not None:
            setattr(question, key, value)
    
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return QuestionPublic.model_validate(question)


async def delete_question(session: AsyncSession, question_id: int) -> bool:
    """Delete a question by ID"""
    statement = select(Question).where(Question.id == question_id)
    question = await session.exec(statement).first()
    
    if not question:
        return False
    
    await session.delete(question)
    await session.commit()
    return True