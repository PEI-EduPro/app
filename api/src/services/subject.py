import logging
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.subject import Subject

logger = logging.getLogger(__name__)

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
    subject = await session.get(Subject, subject_id)
    if not subject:
        return False
    await session.delete(subject)
    await session.commit()
    return True
