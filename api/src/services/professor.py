from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.professor import Professor
from src.models.user import User, UserType
from typing import Optional, List


async def create_professor(
    session: AsyncSession,
    professor_data: dict
) -> Professor:
    """Create a new professor"""
    # First create the User entry
    user = User(
        name=professor_data["name"],
        email=professor_data["email"],
        user_type=UserType.PROFESSOR
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Then create the Professor entry linked to the User
    professor = Professor(id=user.id)
    session.add(professor)
    await session.commit()
    await session.refresh(professor)
    
    return professor


async def get_all_professors(session: AsyncSession) -> List[Professor]:
    """Get all professors from database"""
    statement = select(Professor)
    result = await session.exec(statement)
    return list(result.all())


async def get_professor_by_id(session: AsyncSession, professor_id: int) -> Optional[Professor]:
    """Get a professor by its ID"""
    statement = select(Professor).where(Professor.id == professor_id)
    result = await session.exec(statement)
    return result.first()


async def update_professor(
    session: AsyncSession,
    professor_id: int,
    professor_data: dict
) -> Optional[Professor]:
    """Update a professor by ID"""
    # Get the professor
    professor = await get_professor_by_id(session, professor_id)
    if not professor:
        return None
    
    # Get the associated User to update name and email
    user = await session.get(User, professor_id)
    if not user:
        return None
    
    # Update User fields
    if "name" in professor_data:
        user.name = professor_data["name"]
    if "email" in professor_data:
        user.email = professor_data["email"]
    
    session.add(user)
    await session.commit()
    await session.refresh(professor)
    return professor


async def delete_professor(session: AsyncSession, professor_id: int) -> bool:
    """Delete a professor by ID"""
    professor = await get_professor_by_id(session, professor_id)
    if not professor:
        return False
    
    # Delete the Professor entry (User will be handled by cascade if configured)
    await session.delete(professor)
    
    # Also delete the User entry
    user = await session.get(User, professor_id)
    if user:
        await session.delete(user)
    
    await session.commit()
    return True


async def get_professor_subjects(session: AsyncSession, professor_id: int) -> Optional[List[dict]]:
    """Get all subjects taught by a professor"""
    professor = await get_professor_by_id(session, professor_id)
    if not professor:
        return None
    
    # Access the subjects through the relationship
    await session.refresh(professor, ["subjects"])
    
    return [
        {
            "id": subject.id,
            "subject_id": subject.subject_id,
            "name": subject.name
        }
        for subject in professor.subjects
    ]


async def get_professor_workbooks(session: AsyncSession, professor_id: int) -> Optional[List[dict]]:
    """Get all workbooks created by a professor"""
    professor = await get_professor_by_id(session, professor_id)
    if not professor:
        return None
    
    # Access the workbooks through the relationship
    await session.refresh(professor, ["workbooks"])
    
    return [
        {
            "id": workbook.id,
            "workbook_name": workbook.workbook_name,
            "professor_id": workbook.professor_id
        }
        for workbook in professor.workbooks
    ]
