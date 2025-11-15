from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from src.core.db import get_session
from src.core.deps import get_current_user
from src.models.user import User
from src.models.subject import SubjectUpdate,SubjectCreate,SubjectPublic
from src.services import subject


router = APIRouter()

@router.post("/", response_model=SubjectPublic, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_create: SubjectCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new subject"""
    subject_data = subject_create.model_dump()
    sub = await subject.create_subject(session, subject_data)
    return sub


@router.get("/", response_model=List[SubjectPublic])
async def get_subjects(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all subjects"""
    subjects = await subject.get_all_subjects(session)
    return subjects


@router.get("/{id}", response_model=SubjectPublic)
async def get_subject(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a sub by ID"""
    sub = await subject.get_subject_by_id(session, id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return sub


@router.patch("/{id}", response_model=SubjectPublic)
async def update_subject(
    id: int,
    subject_update: SubjectUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a sub by ID"""
    # Convert to dict and exclude unset fields
    update_data = subject_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    sub = await subject.update_subject(session, id, update_data)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return sub


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a subject by ID"""
    deleted = await subject.delete_subject(session, id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return None