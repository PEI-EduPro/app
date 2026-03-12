from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.core.db import get_session
from src.models.user import User
from src.models.exam_config import ExamConfig
from src.models.waiting_room import WaitingRoom, WaitingRoomCreateRequest, WaitingRoomResponse, WaitingRoomState, WaitingRoomInfoResponse, WaitingRoomMetricsResponse
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
        waiting_room = await waiting_room_service.create_waiting_room_service(
            session=session,
            exam_config_id=request.exam_config_id,
            regent_keycloak_id=user_info.user_id,
            vigilant_keycloak_ids=request.vigilant_keycloak_ids
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

@router.get("/{waiting_room_id}/info", response_model=WaitingRoomInfoResponse)
async def get_waiting_room_info(
    waiting_room_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all information regarding the exam being overseen.
    Includes student list, exam IDs, stats, and state.
    """
    # Verify permission - vigilant or regent
    verify_permission(user_info, [f"/w{waiting_room_id}/vigilant", f"/w{waiting_room_id}/regent"])

    try:
        info = await waiting_room_service.get_waiting_room_info_service(session, waiting_room_id)
        if not info:
            raise HTTPException(status_code=404, detail="Waiting room or associated exam configuration not found.")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve waiting room info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve waiting room info: {str(e)}"
        )

@router.post("/{waiting_room_id}/student_to_exam")
async def associate_students_to_exams(
    waiting_room_id: int,
    qrcode_to_nmec: dict,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Associate a student to an exam by appending to the waiting room's association list.
    Vigilantes and regents can perform this action.
    The payload `qrcode_to_nmec` expects the key to be the exam ID and the value to be the student NMEC.
    """
    # Verify permission
    verify_permission(user_info, [f"/w{waiting_room_id}/vigilant", f"/w{waiting_room_id}/regent"])

    waiting_room = await waiting_room_service.get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=404, detail="Waiting room not found.")
        
    if waiting_room.state != WaitingRoomState.RUNNING:
        raise HTTPException(status_code=400, detail="Waiting room must be in running state to associate students.")

    try:
        # qrcode_to_nmec is a dict: { "exam_id": "student_nmec" }
        for exam_id_str, student_nmec in qrcode_to_nmec.items():
            exam_id = int(exam_id_str)
            await waiting_room_service.associate_student_to_exam_service(
                session=session,
                waiting_room_id=waiting_room_id,
                exam_id=exam_id,
                student_nmec=str(student_nmec)
            )

        return {"message": "Students associated to exams successfully."}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exam ID format. Must be an integer.")
    except Exception as e:
        logger.error(f"Failed to associate students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to associate students to exams: {str(e)}"
        )

@router.get("/{waiting_room_id}/metrics", response_model=WaitingRoomMetricsResponse)
async def get_waiting_room_metrics(
    waiting_room_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Lightweight endpoint to get real-time metrics for an ongoing exam.
    Returns the count of associated exams and associated students.
    """
    # Verify permission
    verify_permission(user_info, [f"/w{waiting_room_id}/vigilant", f"/w{waiting_room_id}/regent"])

    try:
        metrics = await waiting_room_service.get_waiting_room_metrics_service(session, waiting_room_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Waiting room not found.")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve waiting room metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve waiting room metrics: {str(e)}"
        )

@router.patch("/{waiting_room_id}/close", response_model=WaitingRoomResponse)
async def close_waiting_room(
    waiting_room_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Close a waiting room. Checks for association conflicts (e.g. one student to multiple exams).
    If conflicts exist, stops at the CLOSED state and raises an error.
    If no conflicts exist, maps the students to exams and transitions to FINISHED.
    Only the regent of the subject can perform this action.
    """
    waiting_room = await waiting_room_service.get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=404, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    # Verify permission - only regent can close waiting room
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    try:
        updated_room = await waiting_room_service.close_waiting_room_service(session, waiting_room_id)
        
        return WaitingRoomResponse(
            id=updated_room.id,
            exam_config_id=updated_room.exam_config_id,
            state=updated_room.state,
            associations=updated_room.associations,
            message="Waiting room closed successfully. Associations processed."
        )
    except ValueError as ve:
        # Conflicts found, or invalid state. Raise HTTP 400 Bad Request
        logger.warning(f"Failed to close waiting room due to conflicts or invalid state: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to close waiting room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close waiting room: {str(e)}"
        )
