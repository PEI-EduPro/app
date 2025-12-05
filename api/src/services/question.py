import logging
from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.utils import parse_moodle_xml
from src.models.question_option import QuestionOption, QuestionOptionPublic
from src.models.question import Question, QuestionCreate, QuestionPublic, QuestionUpdate
from typing import Optional, List

logger = logging.getLogger(__name__)

async def create_question(
    session: AsyncSession,
    question_data: List[QuestionCreate]
) -> List[QuestionPublic]:
    """Create a new question"""
    questions = [Question.model_validate(x) for x in question_data]
    
    session.add_all(questions)  # More efficient than individual adds
    await session.commit()
    
    for question in questions:
        await session.refresh(question)
    
    return [QuestionPublic.model_validate(q) for q in questions]

async def create_question_XML(
    session: AsyncSession,
    subject_id: int,
    question_xml: str
) -> dict:
    """Create a new question"""
    result = parse_moodle_xml(question_xml)
    
    return result


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


async def get_question_options_by_question_id(session: AsyncSession, question_id: int) -> Optional[List[QuestionOptionPublic]]:
    """Retrieve question_options respective to provided question ID"""
    statement = select(QuestionOption).where(QuestionOption.question_id == question_id)
    result = await session.exec(statement)
    items = result.all() 
    
    validated_items = []
    for item in items:
        try:
            validated_item = QuestionOptionPublic.model_validate(item)
            validated_items.append(validated_item)
        except ValidationError as e:
            logger.error(f"Validation error for item {item.id}: {e}")
    return validated_items
