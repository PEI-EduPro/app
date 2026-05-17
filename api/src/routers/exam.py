import anyio
import base64
import logging
import os
import traceback
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Response, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src import utils
from src.core.db import get_session, async_session
from src.core.deps import get_current_user_info, verify_permission
from src.models.common import MessageResponse
from src.models.email_options import EmailOptionsPayload
from src.models.exam import CorrectByHandRequest
from src.models.exam_config import (
    ExamConfig,
    ExamConfigRead,
    ExamConfigResponse, 
    GenerationStatus, 
    ExamState, 
    ExamSessionResponse, 
    ExamSessionInfoResponse, 
    ExamSessionMetricsResponse, 
    ProfessorExamSessionItem, 
    EvaluateBatchRequest, 
    QRCodeToNMEC
)
from src.models.topic_config import TopicConfig, TopicConfigDTO
from src.models.user import User
from src.models.warning import Warning
from src.services.exam import (
    build_exam_questions,
    correct_by_hand,
    create_configs,
    create_configs_and_exams,
    delete_exam_config,
    generate_exams_task,
    get_exam_by_id,
    get_exam_config_by_id,
    get_exam_configs_by_subject,
    get_exams_by_config_id,
    get_latest_exam_config_id,
    get_subject_id_by_exam_config_id,
    process_student_list_csv,
    create_exam_session_groups_service,
    transition_exam_config_state,
    get_exam_session_info_service,
    associate_student_to_exam_service,
    get_exam_session_metrics_service,
    close_exam_session_service,
    get_professor_exam_sessions,
    notify_student
)
from src.services.omr import evaluate_exam

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
    configs = await get_exam_configs_by_subject(session, subject_id)

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

        response.append(ExamConfigResponse(
            id=config.id,
            subject_id=config.subject_id,
            fraction=config.fraction,
            topic_configs=topic_configs_dto,
            nmec_name_list=config.nmec_name_list,
            num_versions=config.num_versions,
            status=config.status,
            state=config.state,
            associations=config.associations,
            total_exams=config.total_exams,
            associated_exams_count=config.associated_exams_count,
            pictured_exams_count=config.pictured_exams_count
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="subject_id is required in exam_specs")

    verify_permission(user_info, [f"/s{subject_id}/generate_exams", f"/s{subject_id}/regent"])
    try:
        total_exams = exam_specs.get("total_exams", 1) # Total exams
        num_versions = exam_specs.get("number_versions", total_exams) # Unique shuffles
        student_tuples = exam_specs.get("student_tuples", [])  # List of (nmec, name, email)
        vigilant_keycloak_ids = exam_specs.get("vigilant_keycloak_ids", [])

        zip_bytes = await create_configs_and_exams(
            session,
            exam_specs,
            num_versions,
            student_tuples,
            total_exams
        )

        # Create waiting room if vigilant_keycloak_ids provided
        if not vigilant_keycloak_ids:
            vigilant_keycloak_ids = []
        # Get the created exam_config_id from the service
        exam_config_id = await get_latest_exam_config_id(session, subject_id)

        await create_exam_session_groups_service(
            session=session,
            exam_config_id=exam_config_id,
            regent_keycloak_id=user_info.user_id,
            vigilant_keycloak_ids=vigilant_keycloak_ids
        )

        logger.info(f"Successfully generated {total_exams} exam variations.")

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create configs: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exam configuration"
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="subject_id is required in exam_specs")

    verify_permission(user_info, [f"/s{subject_id}/generate_exams", f"/s{subject_id}/regent"])
    
    try:
        total_exams = exam_specs.get("total_exams", 1) # Total exams
        num_versions = exam_specs.get("number_versions", total_exams) # Unique shuffles
        student_tuples = exam_specs.get("student_tuples", [])
        vigilant_keycloak_ids = exam_specs.get("vigilant_keycloak_ids", [])

        # Create configs with PENDING status
        exam_config, topic_configs = await create_configs(session, exam_specs, student_tuples, num_versions)
        exam_config.status = GenerationStatus.PENDING
        session.add(exam_config)
        await session.commit()
        await session.refresh(exam_config)

        # Create waiting room
        if not vigilant_keycloak_ids:
            vigilant_keycloak_ids = []
        
        await create_exam_session_groups_service(
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
            total_exams,
            exam_specs,
            num_versions
        )

        logger.info(f"Started async generation for {total_exams} variations. Config ID: {exam_config.id}")

        tc_result = await session.exec(
            select(TopicConfig)
            .where(TopicConfig.exam_config_id == exam_config.id)
            .options(selectinload(TopicConfig.topic))
        )
        loaded_topic_configs = tc_result.all()

        topic_configs_dto = [
            TopicConfigDTO(
                id=tc.id,
                topic_id=tc.topic_id,
                topic_name=tc.topic.name if tc.topic else "Unknown",
                num_questions=tc.num_questions,
                relative_weight=tc.relative_weight
            ) for tc in loaded_topic_configs
        ]

        return ExamConfigResponse(
            id=exam_config.id,
            subject_id=exam_config.subject_id,
            fraction=exam_config.fraction,
            topic_configs=topic_configs_dto,
            nmec_name_list=exam_config.nmec_name_list,
            num_versions=num_versions,
            status=exam_config.status,
            state=exam_config.state,
            associations=exam_config.associations,
            total_exams=total_exams
        )

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate async generation: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate async exam generation")


@router.get("/config/{exam_config_id}/status")
async def get_config_status(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """Get the current generation status of an exam configuration."""
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

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
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if exam_config.status != GenerationStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Generation is not completed. Current status: {exam_config.status}")

    if not exam_config.zip_path or not os.path.exists(exam_config.zip_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated ZIP file not found on server.")

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
    group_name = await get_subject_id_by_exam_config_id(exam_config_id, session)

    verify_permission(user_info, [f"/s{group_name}/regent"])

    if file.content_type not in ("text/csv", "text/plain", "application/octet-stream"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only CSV files are accepted.")
    
    # Read file contents asynchronously
    contents = await file.read()

    # Always release the file buffer when done
    await file.close()

    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    await process_student_list_csv(session, exam_config_id, contents)    
    return {"message": "Student list stored successfully."}

@router.get("/exam/{exam_config_id}/student_list",response_model=ExamConfigResponse)
async def retrieve_student_list(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    #correct to the waiting room id
    try:
        group_name = await get_subject_id_by_exam_config_id(exam_config_id, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    verify_permission(user_info, [f"/w{group_name}/vigilante", f"/w{group_name}/regent"])

    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    return ExamConfigResponse(
        id=exam_config.id,
        subject_id=exam_config.subject_id,
        fraction=exam_config.fraction,
        topic_configs=exam_config.topic_configs or [],
        nmec_name_list=exam_config.nmec_name_list,
        num_versions=exam_config.num_versions,
        status=exam_config.status,
        state=exam_config.state,
        associations=exam_config.associations,
        total_exams=exam_config.total_exams,
        associated_exams_count=exam_config.associated_exams_count,
        pictured_exams_count=exam_config.pictured_exams_count
    )


@router.delete("/config/{exam_config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam_config_endpoint(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Remove an exam configuration. Only the regent of the subject can do this.
    """
    try:
        subject_id = await get_subject_id_by_exam_config_id(exam_config_id, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    verify_permission(user_info, [f"/s{subject_id}/regent"])

    # Check if session is in PREPARING or COMPLETED state
    exam_config = await session.get(ExamConfig, exam_config_id)
    if not exam_config:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    if exam_config.state not in [ExamState.PREPARING, ExamState.COMPLETED]:
         raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete exam configuration because its state is {exam_config.state}. It must be in 'preparing' or 'completed' state."
            )

    success = await delete_exam_config(session, exam_config_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Deprecated: use POST /api/exams/{exam_config_id}/session/evaluate instead
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

    exam_instance = await get_exam_by_id(session, exam_id)
    if not exam_instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found.")

    subject_id = await get_subject_id_by_exam_config_id(exam_instance.exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    if exam_instance.grade is None or exam_instance.results is None or exam_instance.capture_path is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exam has not been corrected yet.")

    exam_instance.validated = True
    session.add(exam_instance)
    await session.commit()

    return {"status": "success"}


@router.get("/{exam_config_id}/all_exams_info")
async def get_all_exams_info(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get info for all exams in an exam configuration.
    Returns a list of exam info objects with grade, questions breakdown, capture (base64) and correction status.
    Only accessible by the regent of the subject.
    """
    exam_config = await session.get(ExamConfig, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    subject_id = await get_subject_id_by_exam_config_id(exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    try:
        exams = await get_exams_by_config_id(session, exam_config_id)
    except ValueError:
        return []

    exam_config = await get_exam_config_by_id(session, exam_config_id)
    fraction = exam_config.fraction if exam_config else 0

    result = []
    for e in exams:
        corrected = e.grade is not None and e.results is not None and e.capture_path is not None and e.correction_path is not None

        capture_b64 = None
        if corrected and os.path.exists(e.correction_path):
            async with await anyio.open_file(e.correction_path, "rb") as f:
                content = await f.read()
                capture_b64 = base64.b64encode(content).decode("utf-8")
                
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
    e = await get_exam_by_id(session, exam_id)
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found.")

    subject_id = await get_subject_id_by_exam_config_id(e.exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    corrected = e.grade is not None and e.results is not None and e.capture_path is not None and e.correction_path is not None

    capture_b64 = None
    if corrected and os.path.exists(e.correction_path):
        async with await anyio.open_file(e.correction_path, "rb") as f:
            content = await f.read()
            capture_b64 = base64.b64encode(content).decode("utf-8")

    questions = []
    if corrected:
        exam_config = await get_exam_config_by_id(session, e.exam_config_id)
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
    exam_instance = await get_exam_by_id(session, exam_id)
    if not exam_instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found.")

    subject_id = await get_subject_id_by_exam_config_id(exam_instance.exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    try:
        updated = await correct_by_hand(session, exam_id, body.grid)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    exam_config = await get_exam_config_by_id(session, updated.exam_config_id)
    fraction = exam_config.fraction if exam_config else 0

    return {
        "exam_id": updated.id,
        "grade": updated.grade,
        "questions": build_exam_questions(updated, fraction),
    }

# --- Exam Session (formerly Waiting Room) Endpoints ---

@router.patch("/{exam_config_id}/session/start", response_model=ExamSessionResponse)
async def start_exam_session(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Start an exam session (transition from preparing to running).
    """
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if exam_config.state != ExamState.PREPARING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exam session must be in 'preparing' state to be started.")

    try:
        updated = await transition_exam_config_state(session, exam_config_id, ExamState.RUNNING)
        return ExamSessionResponse(
            id=updated.id,
            state=updated.state,
            associations=updated.associations,
            message="Exam session started successfully."
        )
    except Exception as e:
        logger.error(f"Failed to start exam session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start exam session")

@router.get("/{exam_config_id}/session/info", response_model=ExamSessionInfoResponse)
async def get_exam_session_info(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all information regarding the exam session.
    """
    verify_permission(user_info, [f"/w{exam_config_id}/vigilant", f"/w{exam_config_id}/regent"])

    try:
        info = await get_exam_session_info_service(session, exam_config_id, user_info.groups)
        if not info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve exam session info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve session info")

@router.post("/{exam_config_id}/session/student_to_exam", response_model=MessageResponse)
async def associate_student_to_exam_endpoint(
    exam_config_id: int,
    qrcode_to_nmec: QRCodeToNMEC,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Associate a student to an exam during a running session.
    """
    verify_permission(user_info, [f"/w{exam_config_id}/vigilant", f"/w{exam_config_id}/regent"])

    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")
        
    if exam_config.state != ExamState.RUNNING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Student association is only allowed during the 'running' state. Current state: {exam_config.state}")

    try:
        exam_id = int(qrcode_to_nmec.qr)
        student_nmec = qrcode_to_nmec.nmec
        await associate_student_to_exam_service(
            session=session,
            exam_config_id=exam_config_id,
            exam_id=exam_id,
            student_nmec=str(student_nmec)
        )
        return {"message": "Student associated successfully."}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid exam ID format.")
    except Exception as e:
        logger.error(f"Failed to associate student: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to associate student")

@router.get("/{exam_config_id}/session/metrics", response_model=ExamSessionMetricsResponse)
async def get_exam_session_metrics(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get real-time metrics for an ongoing exam session.
    """
    verify_permission(user_info, [f"/w{exam_config_id}/vigilant", f"/w{exam_config_id}/regent"])

    try:
        metrics = await get_exam_session_metrics_service(session, exam_config_id)
        if not metrics:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve session metrics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve metrics")

@router.get("/professor/my-exam-sessions", response_model=list[ProfessorExamSessionItem])
async def list_professor_exam_sessions(
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all exam sessions where the professor is either a regent or vigilant.
    """
    if "professor" not in user_info.realm_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires professor role.")

    try:
        return await get_professor_exam_sessions(session, user_info.user_id, user_info.groups)
    except Exception as e:
        logger.error(f"Failed to retrieve professor exam sessions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve sessions")

@router.patch("/{exam_config_id}/session/close", response_model=ExamSessionResponse)
async def close_exam_session(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Close an exam session and process associations.
    """
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    try:
        updated = await close_exam_session_service(session, exam_config_id)
        return ExamSessionResponse(
            id=updated.id,
            state=updated.state,
            associations=updated.associations,
            message="Exam session closed successfully."
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to close session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to close session")

@router.get("/{exam_config_id}/session/submitted_count")
async def get_submitted_count(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get the number of exams submitted for OMR.
    """
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    exams = await get_exams_by_config_id(session, exam_config_id)
    count = sum(1 for e in exams if e.capture_path is not None)
    return {"submitted_count": count}

@router.post("/{exam_config_id}/session/evaluate")
async def evaluate_session_batch(
    exam_config_id: int,
    body: EvaluateBatchRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Evaluate a batch of exams using OMR.
    """
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if exam_config.state not in [ExamState.CLOSED_AND_CAPTURE, ExamState.WARNING_HANDLING, ExamState.VALIDATION, ExamState.COMPLETED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OMR evaluation is only allowed starting from the 'closed_and_capture' state. Current state: {exam_config.state}")

    exam_data = []
    for b64_str in body.files:
        exam_id, temp_file_path = await utils.decode_base64_image(b64_str)
        exam_instance = await get_exam_by_id(session, exam_id)
        if not exam_instance or exam_instance.exam_config_id != exam_config_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid exam {exam_id}")
        exam_data.append((exam_instance, temp_file_path))

    results = []
    for exam_instance, temp_file_path in exam_data:
        try:
            await evaluate_exam(session, exam_instance, temp_file_path)
            results.append({"exam_id": exam_instance.id, "status": "success"})
        except Exception as e:
            logger.error(f"Error evaluating exam {exam_instance.id}: {e}")
            results.append({"exam_id": exam_instance.id, "status": "error", "detail": str(e)})

    return {"results": results}

@router.post("/{exam_config_id}/session/notify-students")
async def notify_session_students(
    exam_config_id: int,
    email_options: EmailOptionsPayload,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Notify students about their scores.
    """
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

    if exam_config.state != ExamState.COMPLETED:
        raise HTTPException(status_code=400, detail="Exam must be in 'completed' state to notify students.")
    
    stmt = select(Warning).where(Warning.exam_config_id == exam_config_id)
    result = await session.exec(stmt)
    if result.all():
        raise HTTPException(status_code=400, detail="Resolve warnings first.")
    
    exams = await get_exams_by_config_id(session, exam_config_id)
    
    for exam in exams:
        if exam.student_email and exam.nmec:
            if not (exam.capture_path and exam.grade is not None and exam.validated):
                raise HTTPException(status_code=400, detail=f"Exam {exam.id} not ready.")

    for exam in exams:
        if exam.student_email and exam.nmec:
            try:
                await notify_student(session, exam, email_options.model_dump())
            except Exception as e:
                logger.error(f"Failed to send email for exam {exam.id}: {e}")

    return {"message": "Notification process completed."}
