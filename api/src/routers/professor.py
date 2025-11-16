from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from src.core.db import get_session
from src.core.deps import get_current_user
from src.models.user import User
from src.models.professor import ProfessorCreate, ProfessorUpdate, ProfessorPublic, ProfessorRead
from src.services import professor


router = APIRouter()

@router.post("/", response_model=ProfessorPublic, status_code=status.HTTP_201_CREATED)
async def create_professor(
    professor_create: ProfessorCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new professor"""
    professor_data = professor_create.model_dump()
    prof = await professor.create_professor(session, professor_data)
    return prof


@router.get("/", response_model=List[ProfessorPublic])
async def get_professors(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all professors"""
    professors = await professor.get_all_professors(session)
    return professors


@router.get("/{id}", response_model=ProfessorRead)
async def get_professor(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a professor by ID"""
    prof = await professor.get_professor_by_id(session, id)
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor not found"
        )
    return prof


@router.patch("/{id}", response_model=ProfessorPublic)
async def update_professor(
    id: int,
    professor_update: ProfessorUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a professor by ID"""
    # Convert to dict and exclude unset fields
    update_data = professor_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    prof = await professor.update_professor(session, id, update_data)
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor not found"
        )
    return prof


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_professor(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a professor by ID"""
    deleted = await professor.delete_professor(session, id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor not found"
        )
    return None


@router.get("/{id}/subjects", response_model=List[dict])
async def get_professor_subjects(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all subjects taught by a professor"""
    subjects = await professor.get_professor_subjects(session, id)
    if subjects is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor not found"
        )
    return subjects


@router.get("/{id}/workbooks", response_model=List[dict])
async def get_professor_workbooks(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all workbooks created by a professor"""
    workbooks = await professor.get_professor_workbooks(session, id)
    if workbooks is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor not found"
        )
    return workbooks
