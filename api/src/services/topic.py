from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List, Optional

from src.models.topic import Topic,TopicCreate, TopicRead

async def create_topic(session: AsyncSession, data: TopicCreate) -> TopicRead:
    """Create a new topic"""
    topic = Topic(
        subject_id=data.subject_id,
        name=data.name
    )
    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    return TopicRead.model_validate(topic)

async def get_topics_by_subject(session: AsyncSession, subject_id: int) -> List[TopicRead]:
    """Get all topics for a specific subject"""
    query = select(Topic).where(Topic.subject_id == subject_id)
    results = (await session.exec(query)).all()

    return [TopicRead.model_validate(topic) for topic in results]
