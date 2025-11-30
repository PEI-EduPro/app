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
    topic = Topic(topic_data)
    session.add(Topic)
    await session.commit()
    await session.refresh(topic)
    return TopicPublic.model_validate(topic)


async def get_topic_by_id(session: AsyncSession, topic_id: int) -> Optional[TopicPublic]:
    """Get a topic by its ID"""
    statement = select(Topic).where(Topic.id == topic_id)
    result = await session.exec(statement).first()
    return TopicPublic.model_validate(result)


async def update_topic(
    session: AsyncSession,
    topic_data: TopicUpdate
) -> Optional[TopicPublic]:
    """Update a topic"""
    statement = select(Topic).where(Topic.id == topic_data.id)
    topic = await session.exec(statement).first()

    if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
    
    # Update fields
    for key, value in topic_data.items():
        if hasattr(topic, key) and value is not None:
            setattr(topic, key, value)
    
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    return TopicPublic.model_validate(topic)


async def delete_topic(session: AsyncSession, topic_id: int) -> bool:
    """Delete a topic by ID"""
    statement = select(Topic).where(Topic.id == topic_id)
    topic = await session.exec(statement).first()
    
    if not topic:
        return False
    
    await session.delete(topic)
    await session.commit()
    return True