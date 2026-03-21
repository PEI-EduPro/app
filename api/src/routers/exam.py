# src/routers/exam.py
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Response
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.services import exam
from src.core.db import get_session
from src.models.user import User
from src.models.exam_config import ExamConfig, ExamConfigResponse
from src.models.topic_config import TopicConfigDTO
from src.core.deps import get_current_user_info, verify_permission
from src.core.keycloak import keycloak_client
import logging
import traceback

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
            
        response.append(ExamConfigResponse(
            id=config.id,
            subject_id=config.subject_id,
            fraction=config.fraction,
            #creator_keycloak_id=config.creator_keycloak_id,
            topic_configs=topic_configs_dto,
            nmec_name_list=config.nmec_name_list
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
        if vigilant_keycloak_ids:
            from src.services import waiting_room as waiting_room_service
            
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

@router.post("/exam/{exam_config_id}/student_list")
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

    return ExamConfigResponse.model_validate(exam_config)


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

