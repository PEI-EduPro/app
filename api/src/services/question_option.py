from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.question_option import QuestionOption, QuestionOptionCreate, QuestionOptionPublic, QuestionOptionUpdate
from typing import Optional, List


async def create_question(
    session: AsyncSession,
    question_data: QuestionOptionCreate
) -> QuestionOptionPublic:
    """Create a new question_option"""
    question_option = QuestionOption.model_validate(question_data)
    session.add(question_option)
    await session.commit()
    await session.refresh(question_option)
    return QuestionOptionPublic.model_validate(question_option)


async def get_question_option_by_id(session: AsyncSession, question_id: int) -> Optional[QuestionOptionPublic]:
    """Get a question_option by its ID"""
    statement = select(QuestionOption).where(QuestionOption.id == question_id)
    result = await session.exec(statement)
    result = result.one_or_none()
    return QuestionOptionPublic.model_validate(result)


async def update_question(
    session: AsyncSession,
    question_option_data: QuestionOptionUpdate
) -> Optional[QuestionOptionPublic]:
    """Update a question_option"""
    statement = select(QuestionOption).where(QuestionOption.id == question_option_data.id)
    question_option = await session.exec(statement)
    question_option = question_option.one_or_none()

    if not question_option:
            raise HTTPException(status_code=404, detail="QuestionOption not found")
    
    # Update fields
    data = question_option_data.model_dump()
    question_option.sqlmodel_update(data)
    
    session.add(question_option)
    await session.commit()
    await session.refresh(question_option)
    return QuestionOptionPublic.model_validate(question_option)


async def delete_question(session: AsyncSession, question_option_id: int) -> bool:
    """Delete a question_option by ID"""
    statement = select(QuestionOption).where(QuestionOption.id == question_option_id)
    question_option = await session.exec(statement).first()
    
    if not question_option:
        return False
    
    await session.delete(question_option)
    await session.commit()
    return True