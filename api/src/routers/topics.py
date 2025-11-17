from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional

from src.core.db import get_session
from src.models.topic import TopicCreate, TopicRead
from src.services.topic import create_topic, get_topics_by_subject


router = APIRouter()


@router.post("/", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
async def api_create_topic(
    data: TopicCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a topic"""
    return await create_topic(session, data)


@router.get("/", response_model=List[TopicRead])
async def api_get_topics(
    subject_id: int = Query(..., description="Filter by subject id"),
    session: AsyncSession = Depends(get_session)
):
    """Get all topics belonging to a subject"""
    return await get_topics_by_subject(session, subject_id)
