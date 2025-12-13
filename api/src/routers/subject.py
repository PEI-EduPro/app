from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.topic import TopicPublic
from src.core.db import get_session
from src.models.subject import (
    SubjectCreateRequest, 
    SubjectCreateResponse, 
    SubjectRead,
    SubjectUpdate,
)
import src.services.subject as subject_service

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=SubjectCreateResponse)
async def create_subject(
    subject_data: SubjectCreateRequest,
    session: AsyncSession = Depends(get_session)
):
    """Create a new subject."""
    try:
        subject = await subject_service.create_subject(session, subject_data.name)
        return SubjectCreateResponse(id=subject.id, name=subject.name)
    except Exception as e:
        logger.error(f"Error creating subject: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subject")


@router.get("/", response_model=List[SubjectRead])
async def get_subjects(session: AsyncSession = Depends(get_session)):
    """Get all subjects."""
    return await subject_service.get_all_subjects(session)


@router.get("/{subject_id}/topics", response_model=List[tuple[TopicPublic,int]])
async def get_all_topics_by_subject(subject_id: int, session: AsyncSession = Depends(get_session)):
    """Get all subject topics by subject ID."""
    result = await subject_service.get_all_subject_topics(session, subject_id)
    if not result:
        raise HTTPException(status_code=404, detail="Topics not found")
    return result


@router.get("/{subject_id}/all-questions", response_model=dict)
async def get_all_by_subject(subject_id: int, session: AsyncSession = Depends(get_session)):
    """Get subject by ID."""
    result = await subject_service.get_topics_questions_and_options_by_subject_id(session, subject_id)
    if not result:
        raise HTTPException(status_code=404, detail="Subject not found")
    return result


@router.get("/{subject_id}", response_model=SubjectRead)
async def get_subject(subject_id: int, session: AsyncSession = Depends(get_session)):
    """Get subject by ID"""
    subject = await subject_service.get_subject_by_id(session, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.put("/{subject_id}", response_model=SubjectRead)
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update subject."""
    subject = await subject_service.update_subject(session, subject_id, subject_update.name)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(subject_id: int, session: AsyncSession = Depends(get_session)):
    """Delete subject."""
    success = await subject_service.delete_subject(session, subject_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subject not found")
    
