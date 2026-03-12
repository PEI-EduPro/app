from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.core.db import get_session
from src.models.user import User
from src.models.exam_config import ExamConfig
from src.models.waiting_room import WaitingRoom, WaitingRoomCreateRequest, WaitingRoomResponse, WaitingRoomState
import src.services.waiting_room as waiting_room_service
from src.core.deps import get_current_user_info, verify_permission
from src.core.keycloak import keycloak_client
import logging

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
    result = await session.exec(stmt)
    exam_config = result.first()

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
            state=waiting_room.state,
            associations=waiting_room.associations,
            message="Waiting room created successfully."
        )
    except Exception as e:
        logger.error(f"Failed to create waiting room: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create waiting room: {str(e)}"
        )

@router.patch("/{waiting_room_id}/start", response_model=WaitingRoomResponse)
async def start_waiting_room(
    waiting_room_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Start a waiting room (transition from preparation to running).
    Only the regent of the subject can perform this action.
    """
    waiting_room = await waiting_room_service.get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=404, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    # Verify permission - only regent can start waiting room
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if waiting_room.state != WaitingRoomState.PREPARATION:
        raise HTTPException(status_code=400, detail="Waiting room must be in preparation state to be started.")

    try:
        updated_room = await waiting_room_service.update_waiting_room_state(session, waiting_room_id, WaitingRoomState.RUNNING)
        return WaitingRoomResponse(
            id=updated_room.id,
            exam_config_id=updated_room.exam_config_id,
            state=updated_room.state,
            associations=updated_room.associations,
            message="Waiting room started successfully."
        )
    except Exception as e:
        logger.error(f"Failed to start waiting room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start waiting room: {str(e)}"
        )
