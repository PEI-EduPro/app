# src/routers/exam.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel.ext.asyncio.session import AsyncSession
from src.services import exam
from src.core.db import get_session
from src.models.user import User
from src.models.exam_config import ExamConfigResponse
from src.models.topic_config import TopicConfigDTO
from src.core.deps import get_current_user_info
import logging
import traceback

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/subject/{subject_id}/configs", response_model=List[ExamConfigResponse])
async def get_subject_exam_configs(
    subject_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get all exam configurations for a subject.
    """
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
            creator_keycloak_id=config.creator_keycloak_id,
            topic_configs=topic_configs_dto
        ))
        
    return response

@router.post("/generate")
async def generate_exams(
    exam_specs: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_info)
):
    """
    Generate exams based on specifications.
    Returns a ZIP file containing the generated exam PDFs.
    """
    try:
        num_variations = exam_specs.get("num_variations", 1)

        zip_bytes = await exam.create_configs_and_exams(
            session, 
            exam_specs, 
            current_user, 
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