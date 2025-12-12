from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.topic import Topic, TopicCreate, TopicPublic, TopicUpdate
from typing import Optional, List


async def create_topic(
    session: AsyncSession,
    topic_data: TopicCreate
) -> TopicPublic:
    """Create a new topic"""
    topic = Topic.model_validate(topic_data)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    return TopicPublic.model_validate(topic)

async def get_all_topics(session: AsyncSession) -> List[TopicPublic]:
    """Get all topics."""
    result = await session.exec(select(Topic))
    topics = result.all()
    return [TopicPublic.model_validate(topic) for topic in topics]

async def get_topic_by_id(session: AsyncSession, topic_id: int) -> Optional[TopicPublic]:
    """Get a topic by its ID"""
    statement = select(Topic).where(Topic.id == topic_id)
    result = await session.exec(statement)
    topic = result.one_or_none()
    if not topic:
        return None
    return TopicPublic.model_validate(topic)


async def update_topic(
    session: AsyncSession,
    topic_data: TopicUpdate,
    topic_id: int
) -> Optional[TopicPublic]:
    """Update a topic"""
    statement = select(Topic).where(Topic.id == topic_id)
    topic = await session.exec(statement)
    topic = topic.one_or_none()


    if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
    
    data = topic_data.model_dump()
    topic.sqlmodel_update(data)

    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    return TopicPublic.model_validate(topic)


async def delete_topic(session: AsyncSession, topic_id: int) -> bool:
    """Delete a topic by ID"""
    statement = select(Topic).where(Topic.id == topic_id)
    topic = await session.exec(statement)
    topic = topic.one_or_none()
    
    if not topic:
        return False
    
    await session.delete(topic)
    await session.commit()
    return True