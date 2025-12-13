from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.question_option import QuestionOption, QuestionOptionCreate, QuestionOptionPublic, QuestionOptionUpdate
from typing import List, Optional

async def create_question_options(
    session: AsyncSession,
    options_data: List[QuestionOptionCreate]
) -> List[QuestionOptionPublic]:
    """Create multiple question options"""
    options = [QuestionOption.model_validate(x) for x in options_data]
    session.add_all(options)
    await session.commit()
    for option in options:
        await session.refresh(option)
    return [QuestionOptionPublic.model_validate(o) for o in options]

async def update_question_option(
    session: AsyncSession,
    option_id: int,
    option_data: QuestionOptionUpdate
) -> Optional[QuestionOptionPublic]:
    """Update a question option"""
    statement = select(QuestionOption).where(QuestionOption.id == option_id)
    result = await session.exec(statement)
    option = result.one_or_none()
    
    if not option:
        raise HTTPException(status_code=404, detail="Question option not found")
    
    option.sqlmodel_update(option_data.model_dump(exclude_unset=True))
    session.add(option)
    await session.commit()
    await session.refresh(option)
    return QuestionOptionPublic.model_validate(option)

async def delete_question_option(session: AsyncSession, option_id: int) -> bool:
    """Delete a question option"""
    statement = select(QuestionOption).where(QuestionOption.id == option_id)
    result = await session.exec(statement)
    option = result.one_or_none()
    
    if not option:
        return False
    
    await session.delete(option)
    await session.commit()
    return True
