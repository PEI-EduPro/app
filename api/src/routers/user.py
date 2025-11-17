from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.db import get_session
from src.core.deps import get_current_user, require_manager
from src.models.user import User, UserRead, UserRole
from src.services.user import update_user_role

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.put("/{user_id}/role", response_model=UserRead)
async def update_user_role_endpoint(
    user_id: int,
    role: UserRole,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: dict = Depends(require_manager)  # This ensures only managers can access
):
    """Update user role (managers only)"""
    updated_user = await update_user_role(session, user_id, role)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user