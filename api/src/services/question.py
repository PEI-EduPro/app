from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional

from src.models.question import Question
from src.models.topic import Topic
from src.models.question import QuestionCreate, QuestionUpdate, QuestionRead


async def create_question(session: AsyncSession, data: QuestionCreate) -> QuestionRead:
    """Create a new question."""
    question = Question(
        topic_id=data.topic_id,
        question_text=data.question_text
    )
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return QuestionRead.model_validate(question)


async def get_questions_by_subject(session: AsyncSession, subject_id: int) -> List[QuestionRead]:
    """Fetch all questions belonging to a given subject."""
    
    query = (
        select(Question)
        .join(Topic)
        .where(Topic.subject_id == subject_id)
    )
    results = (await session.execute(query)).scalars().all()

    return [QuestionRead.model_validate(q) for q in results]


async def update_question(session: AsyncSession, question_id: int, data: QuestionUpdate) -> Optional[QuestionRead]:
    """Update an existing question."""
    
    question = await session.get(Question, question_id)
    if not question:
        return None
    
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(question, key, value)

    session.add(question)
    await session.commit()
    await session.refresh(question)

    return QuestionRead.model_validate(question)

async def delete_question(session: AsyncSession, question_id: int) -> bool:
    """Delete a question by ID."""

    question = await session.get(Question, question_id)
    if not question:
        return False

    await session.delete(question)
    await session.commit()
    return True
