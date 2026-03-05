import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.core.db import get_session
from src.core.deps import get_current_user_info, verify_permission
from src.models.user import User
from src.models.waiting_room import WaitingRoom, WaitingRoomCreateRequest, WaitingRoomResponse
from src.models.exam_config import ExamConfig
from src.core.keycloak import keycloak_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=WaitingRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_waiting_room(
    request: WaitingRoomCreateRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new waiting room for an exam batch and assign vigilants.
    Only the regent of the subject can perform this action.
    """
    # Fetch ExamConfig to get subject_id
    stmt = select(ExamConfig).where(ExamConfig.id == request.exam_config_id)
    result = await session.execute(stmt)
    exam_config = result.scalar_one_or_none()

    if not exam_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam config {request.exam_config_id} not found."
        )

    # Verify permission - only regent can create waiting room
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    try:
        # Create WaitingRoom in DB
        waiting_room = WaitingRoom(exam_config_id=request.exam_config_id)
        session.add(waiting_room)
        await session.commit()
        await session.refresh(waiting_room)

        # Create Keycloak groups and assign users
        await keycloak_client.create_waiting_room_groups(
            waiting_room_id=waiting_room.id,
            regent_keycloak_id=user_info.user_id,
            vigilant_ids=request.vigilant_keycloak_ids
        )

        return WaitingRoomResponse(
            id=waiting_room.id,
            exam_config_id=waiting_room.exam_config_id,
            message="Waiting room created successfully."
        )
    except Exception as e:
        logger.error(f"Failed to create waiting room: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create waiting room: {str(e)}"
        )
