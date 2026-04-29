# src/routers/exam.py
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Response, BackgroundTasks
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.services import exam
from src.services.exam import build_exam_questions, generate_exams_task
from src.services import waiting_room as waiting_room_service
from src.services.waiting_room import get_waiting_room
from src.services.omr import evaluate_exam
from src.core.db import get_session, async_session
from src.models.user import User
from src.models.exam import Exam, ExamRead, ExamPublic, ExamUpdate, ExamCreate, CorrectByHandRequest
from src.models.exam_config import ExamConfig, ExamConfigResponse, ExamGenerateRequest, GenerationStatus
from src.models.common import MessageResponse, StatusResponse
from src.models.topic_config import TopicConfigDTO
from src.core.deps import get_current_user_info, verify_permission
from src.core.keycloak import keycloak_client
import base64
import json
import logging
import os
import traceback
import cv2
from src import utils

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/subject/{subject_id}/configs", response_model=List[ExamConfigResponse])
async def get_subject_exam_configs(
    subject_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all exam configurations for a subject.
    """
    verify_permission(user_info, [f"/s{subject_id}"])
    configs = await exam.get_exam_configs_by_subject(session, subject_id)

    response = []
    for config in configs:
        topic_configs_dto = []
        for tc in config.topic_configs:
            # Safely access the topic name if it exists
            topic_name = tc.topic.name if tc.topic else "Unknown Topic"

            topic_configs_dto.append(TopicConfigDTO(
                id=tc.id,
                topic_id=tc.topic_id,
                topic_name=topic_name,
                num_questions=tc.num_questions,
                relative_weight=tc.relative_weight
            ))

        # Count exams using async query to avoid lazy loading
        num_variations = len(config.exams) if config.exams is not None else 0

        response.append(ExamConfigResponse(
            id=config.id,
            subject_id=config.subject_id,
            fraction=config.fraction,
            #creator_keycloak_id=config.creator_keycloak_id,
            topic_configs=topic_configs_dto,
            nmec_name_list=config.nmec_name_list,
            num_variations=num_variations
        ))

    return response

@router.post("/generate")
async def generate_exams(
    exam_specs: dict,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Generate exams based on specifications.
    Returns a ZIP file containing the generated exam PDFs.
    """
    subject_id = exam_specs.get("subject_id")
    if not subject_id:
        raise HTTPException(status_code=400, detail="subject_id is required in exam_specs")

    verify_permission(user_info, [f"/s{subject_id}/generate_exams", f"/s{subject_id}/regent"])
    try:
        num_variations = exam_specs.get("num_variations", 1)
        professors = exam_specs.get("professors", [])
        student_tuples = exam_specs.get("student_tuples", [])  # List of (nmec, name, email)
        vigilant_keycloak_ids = exam_specs.get("vigilant_keycloak_ids", [])

        zip_bytes = await exam.create_configs_and_exams(
            session,
            exam_specs,
            num_variations,
            student_tuples
        )

        # Create waiting room if vigilant_keycloak_ids provided
        if not vigilant_keycloak_ids:
            vigilant_keycloak_ids = []
        # Get the created exam_config_id from the service
        exam_config_id = await exam.get_latest_exam_config_id(session, subject_id)

        await waiting_room_service.create_waiting_room_service(
            session=session,
            exam_config_id=exam_config_id,
            regent_keycloak_id=user_info.user_id,
            vigilant_keycloak_ids=vigilant_keycloak_ids
        )

        logger.info(f"Successfully generated {num_variations} exam variations.")

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=exams.zip"}
        )

    except ValueError as ve:
        logger.warning(f"Validation error during config creation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to create configs: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.post("/generate_async", response_model=ExamConfigResponse)
async def generate_exams_async(
    exam_specs: dict,
    background_tasks: BackgroundTasks,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Generate exams asynchronously.
    Returns the ExamConfig object immediately.
    Status can be tracked via GET /config/{id}
    """
    subject_id = exam_specs.get("subject_id")
    if not subject_id:
        raise HTTPException(status_code=400, detail="subject_id is required in exam_specs")

    verify_permission(user_info, [f"/s{subject_id}/generate_exams", f"/s{subject_id}/regent"])
    
    try:
        num_variations = exam_specs.get("num_variations", 1)
        student_tuples = exam_specs.get("student_tuples", [])
        vigilant_keycloak_ids = exam_specs.get("vigilant_keycloak_ids", [])

        # Create configs with PENDING status
        exam_config, topic_configs = await exam.create_configs(session, exam_specs, student_tuples)
        exam_config.status = GenerationStatus.PENDING
        session.add(exam_config)
        await session.commit()
        await session.refresh(exam_config)

        # Create waiting room
        if not vigilant_keycloak_ids:
            vigilant_keycloak_ids = []
        
        await waiting_room_service.create_waiting_room_service(
            session=session,
            exam_config_id=exam_config.id,
            regent_keycloak_id=user_info.user_id,
            vigilant_keycloak_ids=vigilant_keycloak_ids
        )

        # Schedule background task
        background_tasks.add_task(
            generate_exams_task,
            async_session,
            exam_config.id,
            num_variations,
            exam_specs
        )

        logger.info(f"Started async generation for {num_variations} variations. Config ID: {exam_config.id}")

        topic_configs_dto = [
            TopicConfigDTO(
                id=tc.id,
                topic_id=tc.topic_id,
                topic_name=tc.topic.name if tc.topic else "Unknown",
                num_questions=tc.num_questions,
                relative_weight=tc.relative_weight
            ) for tc in topic_configs
        ]

        return ExamConfigResponse(
            id=exam_config.id,
            subject_id=exam_config.subject_id,
            fraction=exam_config.fraction,
            topic_configs=topic_configs_dto,
            nmec_name_list=exam_config.nmec_name_list,
            num_variations=0, # Will be updated by task
            status=exam_config.status
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to initiate async generation: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{exam_config_id}/status")
async def get_config_status(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Get the current generation status of an exam configuration."""
    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    return {
        "id": exam_config.id,
        "status": exam_config.status,
        "is_ready": exam_config.status == GenerationStatus.COMPLETED
    }


@router.get("/config/{exam_config_id}/download")
async def download_exam_zip(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Download the generated ZIP file for an exam configuration."""
    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if exam_config.status != GenerationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Generation is not completed. Current status: {exam_config.status}")

    if not exam_config.zip_path or not os.path.exists(exam_config.zip_path):
        raise HTTPException(status_code=404, detail="Generated ZIP file not found on server.")

    return FileResponse(
        path=exam_config.zip_path,
        filename=os.path.basename(exam_config.zip_path),
        media_type="application/zip"
    )


@router.post("/exam/{exam_config_id}/student_list", response_model=MessageResponse)
async def store_student_list(
    exam_config_id: int,
    file: UploadFile = File(...),
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Store information in csv file as a dict of nmec: student_name
    """
    group_name = await exam.get_subject_id_by_exam_config_id(exam_config_id, session)

    verify_permission(user_info, [f"/s{group_name}/regent"])

    if file.content_type not in ("text/csv", "text/plain", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
    
    # Read file contents asynchronously
    contents = await file.read()

    # Always release the file buffer when done
    await file.close()

    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    await exam.process_student_list_csv(session, exam_config_id, contents)    
    return {"message": "Student list stored successfully."}

@router.get("/exam/{exam_config_id}/student_list",response_model=ExamConfigResponse)
async def retrieve_student_list(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    #correct to the waiting room id
    try:
        group_name = await exam.get_subject_id_by_exam_config_id(exam_config_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    verify_permission(user_info, [f"/w{group_name}/vigilante", f"/w{group_name}/regent"])

    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    # Count exams using async query to avoid lazy loading
    num_variations = len(exam_config.exams) if exam_config.exams is not None else 0

    return ExamConfigResponse(
        id=exam_config.id,
        subject_id=exam_config.subject_id,
        fraction=exam_config.fraction,
        topic_configs=exam_config.topic_configs or [],
        nmec_name_list=exam_config.nmec_name_list,
        num_variations=num_variations
    )


@router.delete("/config/{exam_config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam_config(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Remove an exam configuration. Only the regent of the subject can do this.
    """
    try:
        subject_id = await exam.get_subject_id_by_exam_config_id(exam_config_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    verify_permission(user_info, [f"/s{subject_id}/regent"])

    success = await exam.delete_exam_config(session, exam_config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Deprecated: use POST /api/waiting-rooms/{waiting_room_id}/evaluate instead
# @router.post("/evaluate")
# async def evaluate_exam_omr(...)
    

    



@router.post("/{exam_id}/validate")
async def validate_exam(
    exam_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    The regent validates that an exam has been rightfully corrected.
    This is to help the regent understand the exams he has already validated.
    """

    exam_instance = await exam.get_exam_by_id(session, exam_id)
    if not exam_instance:
        raise HTTPException(status_code=404, detail="Exam not found.")

    subject_id = await exam.get_subject_id_by_exam_config_id(exam_instance.exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    if exam_instance.grade is None or exam_instance.results is None or exam_instance.capture_path is None:
        raise HTTPException(status_code=400, detail="Exam has not been corrected yet.")

    exam_instance.validated = True
    session.add(exam_instance)
    await session.commit()

    return {"status": "success"}


@router.get("/{waiting_room_id}/all_exams_info")
async def get_all_exams_info(
    waiting_room_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get info for all exams in an exam configuration, identified by waiting room ID.
    Returns a list of exam info objects with grade, questions breakdown, capture (base64) and correction status.
    Only accessible by the regent of the subject.
    """
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise HTTPException(status_code=404, detail="Waiting room not found.")
    exam_config_id = waiting_room.exam_config_id

    subject_id = await exam.get_subject_id_by_exam_config_id(exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    try:
        exams = await exam.get_exams_by_config_id(session, exam_config_id)
    except ValueError:
        return []

    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    fraction = exam_config.fraction if exam_config else 0

    result = []
    for e in exams:
        corrected = e.grade is not None and e.results is not None and e.capture_path is not None

        capture_b64 = None
        if corrected and os.path.exists(e.capture_path):
            with open(e.capture_path, "rb") as f:
                capture_b64 = base64.b64encode(f.read()).decode("utf-8")

        result.append({
            "corrected": corrected,
            "nmec": e.nmec,
            "validated": e.validated,
            "grade": e.grade,
            "exam_id": e.id,
            "capture": capture_b64,
            "questions": build_exam_questions(e, fraction),
        })

    return result




@router.get("/{exam_id}/exam_info")
async def get_exam_info(
    exam_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get info for a single exam by ID.
    Returns grade, questions breakdown, capture (base64) and correction status.
    Returns 404 if the exam is not found. Only accessible by the regent of the subject.
    """
    e = await exam.get_exam_by_id(session, exam_id)
    if not e:
        raise HTTPException(status_code=404, detail="Exam not found.")

    subject_id = await exam.get_subject_id_by_exam_config_id(e.exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    corrected = e.grade is not None and e.results is not None and e.capture_path is not None

    capture_b64 = None
    if corrected and os.path.exists(e.capture_path):
        with open(e.capture_path, "rb") as f:
            capture_b64 = base64.b64encode(f.read()).decode("utf-8")

    questions = []
    if corrected:
        exam_config = await exam.get_exam_config_by_id(session, e.exam_config_id)
        fraction = exam_config.fraction if exam_config else 0
        questions = build_exam_questions(e, fraction)

    return {
        "corrected": corrected,
        "nmec": e.nmec,
        "validated": e.validated,
        "grade": e.grade,
        "exam_id": e.id,
        "capture": capture_b64,
        "questions": questions,
    }


@router.post("/{exam_id}/correct_by_hand_job")
async def correct_by_hand_job(
    exam_id: int,
    body: CorrectByHandRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Manually correct an exam by providing the filled grid.
    The grade is recomputed server-side from the answer key — the client-supplied grade is ignored.
    Only accessible by the regent of the subject.
    """
    exam_instance = await exam.get_exam_by_id(session, exam_id)
    if not exam_instance:
        raise HTTPException(status_code=404, detail="Exam not found.")

    subject_id = await exam.get_subject_id_by_exam_config_id(exam_instance.exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    try:
        updated = await exam.correct_by_hand(session, exam_id, body.grid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    exam_config = await exam.get_exam_config_by_id(session, updated.exam_config_id)
    fraction = exam_config.fraction if exam_config else 0

    return {
        "exam_id": updated.id,
        "grade": updated.grade,
        "questions": build_exam_questions(updated, fraction),
    }
