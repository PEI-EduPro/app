from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.subject import Subject
from typing import Optional, List


async def create_subject(
    session: AsyncSession,
    subject_data: dict
) -> Subject:
    """Create a new subject"""
    subject = Subject(**subject_data)
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject


async def get_all_subjects(session: AsyncSession) -> List[Subject]:
    """Get all subjects from database"""
    statement = select(Subject)
    result = await session.exec(statement)
    return list(result.all())


async def get_subject_by_id(session: AsyncSession, subject_id: int) -> Optional[Subject]:
    """Get a subject by its ID"""
    statement = select(Subject).where(Subject.id == subject_id)
    result = await session.exec(statement)
    return result.first()


async def update_subject(
    session: AsyncSession,
    subject_data: dict
) -> Optional[Subject]:
    """Update a subject by ID"""
    # Get the subject
    subject = await get_subject_by_id(session, subject_id)
    if not subject:
        return None
    
    # Update fields
    for key, value in subject_data.items():
        if hasattr(subject, key) and value is not None:
            setattr(subject, key, value)
    
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject


async def delete_subject(session: AsyncSession, subject_id: int) -> bool:
    """Delete a subject by ID"""
    subject = await get_subject_by_id(session, subject_id)
    if not subject:
        return False
    
    await session.delete(subject)
    await session.commit()
    return True