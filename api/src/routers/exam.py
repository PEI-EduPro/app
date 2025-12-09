# src/routers/exam.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel.ext.asyncio.session import AsyncSession
from src.services import exam
from src.core.db import get_session
from src.models.user import User
from src.core.deps import get_current_user_info
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate")
async def generate_exams(
    exam_specs: dict, # Receive the request body data
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_info)
):
    """
    Generate exams based on specifications.
    Returns a ZIP file containing the generated exam PDFs.
    """
    try:
        # Extract number of variations desired (default to 1)
        num_variations = exam_specs.get("num_variations", 1)

        # Generate exams and get ZIP bytes
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
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating exams."
        )

    