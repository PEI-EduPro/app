import logging
from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.utils import parse_moodle_xml
from src.models.question_option import QuestionOption, QuestionOptionPublic
from src.models.question import Question, QuestionCreate, QuestionPublic, QuestionUpdate
from src.models.topic import Topic
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
    """Create topics, questions and options from Moodle XML"""
    parsed = parse_moodle_xml(question_xml)
    
    created_topics = 0
    created_questions = 0
    created_options = 0
    
    for topic_data in parsed.get("topics", []):
        # Check if topic exists, create if not
        result = await session.exec(select(Topic).where(Topic.name == topic_data["name"], Topic.subject_id == subject_id))
        topic = result.first()
        
        if not topic:
            topic = Topic(name=topic_data["name"], subject_id=subject_id)
            session.add(topic)
            await session.flush()
            created_topics += 1
        
        for q_data in topic_data.get("questions", []):
            # Create question
            question = Question(topic_id=topic.id, question_text=q_data["text"])
            session.add(question)
            await session.flush()
            created_questions += 1
            
            for opt in q_data.get("options", []):
                # Create option (value=True if fraction > 0)
                option = QuestionOption(
                    question_id=question.id,
                    option_text=opt["text"],
                    value=opt["fraction"] > 0
                )
                session.add(option)
                created_options += 1
    
    await session.commit()
    
    return {
        "topics_created": created_topics,
        "questions_created": created_questions,
        "options_created": created_options
    }


async def get_question_by_id(session: AsyncSession, question_id: int) -> Optional[QuestionPublic]:
    """Get a question by its ID"""
    statement = select(Question).where(Question.id == question_id)
    result = await session.exec(statement)
    result = result.one_or_none()
    if result is None:
        return None
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
    result = await session.execute(statement)
    items = result.scalars().all()
    
    validated_items = []
    for item in items:
        try:
            validated_item = QuestionOptionPublic.model_validate(item)
            validated_items.append(validated_item)
        except ValidationError as e:
            logger.error(f"Validation error for item {item.id}: {e}")
    return validated_items
