import logging
from typing import List, Optional, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.question_option import QuestionOption
from src.models.question import Question
from src.models.topic import Topic, TopicPublic
from src.models.subject import Subject

logger = logging.getLogger(__name__)
from sqlalchemy.orm import joinedload


async def get_topics_questions_and_options_by_subject_id(
    session: AsyncSession, subject_id: int
) -> dict:
    #não tocar nesta query, está bem cozinhada
    stmt = (
        select(Subject)
        .where(Subject.id == subject_id)
        .options(
            joinedload(Subject.topics)
                .joinedload(Topic.questions)
                .joinedload(Question.question_options)
        )
    )

    result = await session.exec(stmt)
    subject: Subject | None = result.unique().one_or_none()

    if not subject:
        return {}

    result_subject = {
        "subject_name": subject.name,
        "subject_id":subject.id,
        "subject_topics": {}
    }

    for topic in subject.topics:
        topic_data = {
            "topic_name": topic.name,
            "topic_id":topic.id,
            "topic_questions": {}
        }

        for question in topic.questions:
            question_data = {
                "question_text": question.question_text,
                "question_id":question.id,
                "question_options": {},
                "answer" : ""
            }

            for option in question.question_options:
                question_data["question_options"][option.id] = option.option_text

                if option.value:
                    question_data["answer"] = option.id

            topic_data["topic_questions"][question.id] = question_data

        result_subject["subject_topics"][topic.id] = topic_data

    return result_subject

async def get_all_subject_topics(session: AsyncSession, subject_id: int) -> List[Tuple[TopicPublic, int]]:
    topics_result = await session.exec(select(Topic).where(Topic.subject_id == subject_id))
    topics = topics_result.all()
    
    result = []
    for topic in topics:
        questions_result = await session.exec(select(Question).where(Question.topic_id == topic.id))
        count = len(questions_result.all())
        result.append((TopicPublic.model_validate(topic), count))
    
    return result
    


async def create_subject(session: AsyncSession, name: str) -> Subject:
    """Create a new subject."""
    subject = Subject(name=name)
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject

async def get_all_subjects(session: AsyncSession) -> List[Subject]:
    """Get all subjects."""
    result = await session.exec(select(Subject))
    return list(result.all())

async def get_subject_by_id(session: AsyncSession, subject_id: int) -> Optional[Subject]:
    """Get subject by ID."""
    return await session.get(Subject, subject_id)

async def update_subject(session: AsyncSession, subject_id: int, name: Optional[str]) -> Optional[Subject]:
    """Update subject."""
    subject = await session.get(Subject, subject_id)
    if not subject:
        return None
    if name:
        subject.name = name
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject

async def delete_subject(session: AsyncSession, subject_id: int) -> bool:
    """Delete subject."""
    from src.models.exam_config import ExamConfig
    from src.models.exam import Exam
    
    subject = await session.get(Subject, subject_id)
    if not subject:
        return False
    
    # Delete exams first, then exam_configs
    result = await session.exec(select(ExamConfig).where(ExamConfig.subject_id == subject_id))
    exam_configs = result.all()
    for ec in exam_configs:
        exams_result = await session.exec(select(Exam).where(Exam.exam_config_id == ec.id))
        for exam in exams_result.all():
            await session.delete(exam)
        await session.delete(ec)
    
    await session.delete(subject)
    await session.commit()
    return True
