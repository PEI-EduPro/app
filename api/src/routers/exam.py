# src/routers/exam.py
import csv
import io
import json
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Response
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.services import exam
from src.core.db import get_session
from src.models.user import User
from src.models.exam_config import ExamConfig, ExamConfigResponse
from src.models.topic_config import TopicConfigDTO
from src.models.waiting_room import WaitingRoom, WaitingRoomCreateRequest, WaitingRoomResponse
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

        zip_bytes = await exam.create_configs_and_exams(
            session, 
            exam_specs, 
            #current_user, 
            num_variations
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

@router.post("/waiting-room", response_model=WaitingRoomResponse, status_code=status.HTTP_201_CREATED)
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
            message="Waiting room created successfully."
        )
    except Exception as e:
        logger.error(f"Failed to create waiting room: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create waiting room: {str(e)}"
        )
    
@router.post("exam/{exam_config_id}/student_list")
async def store_student_list(
    exam_config_id: int,
    file: UploadFile = File(...),
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Store information in csv file as a dict of nmec: student_name
    """
    group_name = exam.get_subject_id_by_exam_config_id(exam_config_id,session)

    verify_permission(user_info, [f"/s{group_name}/regent"])

    if file.content_type not in ("text/csv", "text/plain", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
    
    # Read file contents asynchronously
    contents = await file.read()
    
    # Decode bytes and wrap in StringIO for the csv reader
    csv_text = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_text))
    
    nmec_dict = {}

    for row in reader:
        nmec = row.get("nmec")
        name = row.get("name")
        if nmec and name:
            nmec_dict[nmec] = name
            
    nmec_name_list = json.dumps(nmec_dict) #to unmarshall use json.loads(nmec_name_list)
    
    # Always release the file buffer when done
    await file.close()

    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")
    
    await exam.store_student_list(session, exam_config_id, nmec_name_list)
    
    return {"message": "Student list stored successfully."}

@router.get("exam/{exam_config_id}/student_list",response_model=ExamConfigResponse)
async def retrieve_student_list(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    #correct to the waiting room id
    group_name = exam.get_subject_id_by_exam_config_id(exam_config_id,session)

    verify_permission(user_info, [f"/w{group_name}/vigilante", f"/w{group_name}/regent"])

    exam_config = exam.get_exam_config_by_id(session,exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    return ExamConfigResponse.model_validate(exam_config)


@router.post("exam/{exam_config_id}/student_to_exam")
async def associate_students_to_exams(
    exam_config_id: int,
    qrcode_to_nmec: dict,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    #correct to the waiting room id
    group_name = exam.get_subject_id_by_exam_config_id(exam_config_id,session)

    verify_permission(user_info, [f"/w{group_name}/vigilante", f"/w{group_name}/regent"])
    #for now the qrcode is just the exam id
    exams = exam.get_exams_by_config_id(session,exam_config_id)

    if not exams:
        raise HTTPException(status_code=404, detail="Exams not found.")
    
    

    return ExamConfigResponse.model_validate(exam_config)
