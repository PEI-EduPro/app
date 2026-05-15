import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src import utils
from src.core.db import get_session
from src.core.deps import get_current_user_info, verify_permission
from src.models.common import MessageResponse
from src.models.email_options import EmailOptionsPayload
from src.models.exam_config import ExamConfig
from src.models.user import User
from src.models.waiting_room import WaitingRoomCreateRequest, WaitingRoomResponse, WaitingRoomState, WaitingRoomInfoResponse, WaitingRoomMetricsResponse, ProfessorWaitingRoomItem, EvaluateBatchRequest, QRCodeToNMEC
from src.models.warning import Warning
from src.services.exam import get_exam_by_id, get_exams_by_config_id, notify_student
from src.services.omr import evaluate_exam
from src.services.waiting_room import (
    associate_student_to_exam_service,
    close_waiting_room_service,
    create_waiting_room_service,
    get_professor_waiting_rooms,
    get_waiting_room,
    get_waiting_room_info_service,
    get_waiting_room_metrics_service,
    update_waiting_room_state,
)

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
        waiting_room = await create_waiting_room_service(
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
            detail="Failed to create waiting room"
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
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    # Verify permission - only regent can start waiting room
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if waiting_room.state != WaitingRoomState.PREPARATION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Waiting room must be in preparation state to be started.")

    try:
        updated_room = await update_waiting_room_state(session, waiting_room_id, WaitingRoomState.RUNNING)
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
            detail="Failed to start waiting room"
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
        info = await get_waiting_room_info_service(session, waiting_room_id, user_info.groups)
        if not info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waiting room or associated exam configuration not found.")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve waiting room info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve waiting room info"
        )

@router.post("/{waiting_room_id}/student_to_exam", response_model=MessageResponse)
async def associate_students_to_exams(
    waiting_room_id: int,
    qrcode_to_nmec: QRCodeToNMEC,
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

    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waiting room not found.")
        
    if waiting_room.state != WaitingRoomState.RUNNING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Waiting room must be in running state to associate students.")

    try:
        exam_id = int(qrcode_to_nmec.qr)
        student_nmec = qrcode_to_nmec.nmec
        await associate_student_to_exam_service(
            session=session,
            waiting_room_id=waiting_room_id,
            exam_id=exam_id,
            student_nmec=str(student_nmec)
        )

        return {"message": "Student associated to exams successfully."}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid exam ID format. Must be an integer.")
    except Exception as e:
        logger.error(f"Failed to associate students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to associate student to exam"
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
        metrics = await get_waiting_room_metrics_service(session, waiting_room_id)
        if not metrics:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waiting room not found.")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve waiting room metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve waiting room metrics"
        )


@router.get("/professor/my-waiting-rooms", response_model=list[ProfessorWaitingRoomItem])
async def list_professor_waiting_rooms(
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all waiting rooms where the professor is either a regent or vigilant.
    
    Returns a flat list of waiting rooms with subject information:
    [
        {
            "subject_id": 1,
            "subject_name": "Mathematics",
            "waiting_room_id": 5,
            "state": "preparation" | "running" | "closed",
            "role": "regent" | "vigilant"
        }
    ]
    
    Only accessible by users with the professor role.
    """
    # Verify professor role
    if "professor" not in user_info.realm_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires the professor role."
        )

    try:
        waiting_rooms = await get_professor_waiting_rooms(
            session=session,
            professor_keycloak_id=user_info.user_id,
            professor_groups=user_info.groups
        )
        return waiting_rooms
    except Exception as e:
        logger.error(f"Failed to retrieve professor waiting rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve waiting rooms: {str(e)}"
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
    If no conflicts exist, maps the students to exams and keeps the room in the CLOSED state.
    Only the regent of the subject can perform this action.
    """
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    # Verify permission - only regent can close waiting room
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    try:
        updated_room = await close_waiting_room_service(session, waiting_room_id)
        
        return WaitingRoomResponse(
            id=updated_room.id,
            exam_config_id=updated_room.exam_config_id,
            state=updated_room.state,
            associations=updated_room.associations,
            message="Waiting room closed successfully. Associations processed."
        )
    except ValueError as ve:
        logger.warning(f"Failed to close waiting room due to conflicts or invalid state: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to close waiting room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close waiting room: {str(e)}"
        )


@router.get("/{waiting_room_id}/submitted_count")
async def get_submitted_exams_count(
    waiting_room_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get the number of exams that have been submitted for OMR correction (i.e. have a capture_path).
    Only accessible by the regent of the subject.
    """
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    exams = await get_exams_by_config_id(session, waiting_room.exam_config_id)
    count = sum(1 for e in exams if e.capture_path is not None)

    return {"submitted_count": count}

@router.post("/{waiting_room_id}/evaluate")
async def evaluate_exam_batch(
    waiting_room_id: int,
    body: EvaluateBatchRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Evaluate a batch of exams using OMR. Only the regent of the subject can perform this.
    The waiting room must be in the CLOSED state.
    All exams must belong to the waiting room's exam_config.

    body.files: list of base64-encoded image strings (optionally with data URI prefix).
    """
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if waiting_room.state != WaitingRoomState.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Waiting room must be in the closed state to evaluate exams.")

    # Read QR codes and validate all exams belong to this waiting room's exam_config
    exam_data = []
    for b64_str in body.files:
        exam_id, temp_file_path = utils.decode_base64_image(b64_str)
        exam_instance = await get_exam_by_id(session, exam_id)
        if not exam_instance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Exam {exam_id} not found.")
        if exam_instance.exam_config_id != waiting_room.exam_config_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exam {exam_id} does not belong to this waiting room's exam configuration."
            )
        exam_data.append((exam_instance, temp_file_path))

    # Process the batch
    results = []
    for exam_instance, temp_file_path in exam_data:
        try:
            await evaluate_exam(session, exam_instance, temp_file_path)
            results.append({"exam_id": exam_instance.id, "status": "success"})
        except Exception as e:
            logger.error(f"Error evaluating exam {exam_instance.id}: {e}")
            logger.error(traceback.format_exc())
            results.append({
                "exam_id": exam_instance.id,
                "status": "error",
                "detail": "Internal error while evaluating exam."
            })

    has_errors = any(r["status"] == "error" for r in results)
    has_success = any(r["status"] == "success" for r in results)

    if has_errors and not has_success:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=results)
    if has_errors:
        return JSONResponse(status_code=status.HTTP_207_MULTI_STATUS, content={"results": results})
    return {"results": results}

@router.post("/{waiting_room_id}/notify-students")
async def notify_students_via_email(
    waiting_room_id: int,
    email_options: EmailOptionsPayload,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Notify students about their exam score.
    """

    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=404, detail="Waiting room not found.")

    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if waiting_room.state != WaitingRoomState.CLOSED:
        raise HTTPException(status_code=400, detail="Waiting room must be in the closed state to notify students.")
    
    # Check if waiting room has any warnings pending resolution
    stmt = select(Warning).where(Warning.exam_config_id == exam_config.id)
    result = await session.exec(stmt)
    pending_warnings = result.all()
    
    if pending_warnings:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot notify students. There are {len(pending_warnings)} pending warning(s) that must be resolved first."
        )
    
    exams = await get_exams_by_config_id(session, exam_config.id)
    
    # Pre-Notification Checks
    for exam in exams:
        # Only alert for exams that actually have an association
        if exam.student_email and exam.nmec and exam.student_name:

            # Check if exam was corrected
            if not (exam.capture_path and exam.correction_path and exam.grade is not None and exam.results):
                raise HTTPException(
                    status_code=400,
                    detail=f"Exam {exam.id} has not yet been corrected!"
                )

            # Check if exam was manually validated by the professor
            if not exam.validated:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot notify students. Exam {exam.id} has not been validated."
                )

    for exam in exams:
        # Check if exam is associated with a student (skips unused exams)
        if not (exam.student_email and exam.nmec and exam.student_name):
            logger.warning(f"Exam {exam.id} is not associated with any student!")
            continue

        try:
            await notify_student(session, exam, email_options.model_dump())
        except Exception as e:
            logger.error(f"Failed to send email for exam {exam.id}: {e}")

    return {"message": f"Successfully notified students in waiting room {waiting_room_id}."}