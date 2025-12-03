# src/routers/subject.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.services import exam


from src.core.db import get_session
from src.core.deps import require_subject_regent, verify_regent_exists # Import the new dependency
from src.models.topic import Topic, TopicCreate, TopicPublic
from src.models.user import User
from src.core.deps import get_current_user_info
import logging
from sqlmodel import select


logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=str)#, dependencies=[Depends(require_subject_regent)])
async def generate_exams(
    exam_specs: dict, # Receive the request body data
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_info)
):
    """
    Create a new topic in the database.
    Requires the 'regent' role.
    """
    #logger.info(f"User '{current_user.user_id}' is attempting to create topic '{topic_data.name}'")

    try:
        # 1. Verify current_user is regent BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have current_user
        #regent_info = await verify_regent_exists(current_user.user_id)

        # 2. Create the Topic in the local database
        exam_config_id = await exam.create_configs_and_exams(session,exam_specs,current_user)

        logger.info(f"Configs created succesfully, exam config id: '{exam_config_id}'")

        # Return success response
        return "FAAAAAAAAAAAAH"

    except ValueError as ve:
        # Handle specific validation errors like regent not found (caught by require_subject_regent)
        logger.warning(f"Validation error during config creation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation (e.g., DB error, Keycloak error)
        logger.error(f"Failed to create configs: {e}")
        logger.exception(e) # Log the full traceback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the topic in the database."
        )
    

@router.post("/generate-XML", response_model=str)#, dependencies=[Depends(require_subject_regent)])
async def generate_exams_XML(
    exam_specs: dict, # Receive the request body data
    session: AsyncSession = Depends(get_session),
    #current_user: User = Depends(get_current_user_info)
):
    pass

# ... (keep existing endpoints like GET, PUT, etc.) ...

# @router.get("/{id}", response_model=TopicPublic)
# async def read_topic(
#     id: int,
#     session: AsyncSession = Depends(get_session)
# ):
#     """Get topic info from provided name"""
#     # FIX: Use select statement filtering by name
#     result = await topic.get_topic_by_id(session,id)
    
#     if not result:
#         raise HTTPException(status_code=404, detail="Topic not found")
#     return TopicPublic.model_validate(result)
    
    