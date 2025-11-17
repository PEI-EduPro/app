from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.models.question_option import QuestionOption
from src.models.question_option import QuestionOptionCreate,QuestionOptionRead

async def create_question_options(
    session: AsyncSession, 
    question_id: int, 
    options: List[QuestionOptionCreate]
):
    created_options = []

    for opt in options:
        option = QuestionOption(
            question_id=question_id,
            option_text=opt.option_text,
            fraction=opt.fraction,
            order_position=opt.order_position
        )
        session.add(option)
        created_options.append(option)

    await session.commit()

    for opt in created_options:
        await session.refresh(opt)

    return [QuestionOptionRead.model_validate(opt) for opt in created_options]

async def delete_question_option(
    session: AsyncSession, 
    question_id: int, 
    option_id: int
) -> bool:
    """Delete a specific option from a question."""
    
    query = (
        select(QuestionOption)
        .where(QuestionOption.id == option_id)
        .where(QuestionOption.question_id == question_id)
    )

    result = await session.execute(query)
    option = result.scalar_one_or_none()

    if not option:
        return False

    await session.delete(option)
    await session.commit()
    return True
