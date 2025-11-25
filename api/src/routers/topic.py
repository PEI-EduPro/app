# src/routers/subject.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.db import get_session
from src.core.deps import require_subject_regent, verify_regent_exists # Import the new dependency
from src.models.topic import Topic, TopicCreateRequest, TopicCreateResponse, TopicRead
from src.models.user import User
from src.core.deps import get_current_user_info
import logging


logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/topic/{subject}", response_model=TopicCreateResponse, dependencies=[Depends(require_subject_regent)])
async def create_topic(
    subject: str,
    topic_data: TopicCreateRequest, # Receive the request body data
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_info)
):
    """
    Create a new topic in the database.
    Requires the 'regent' role.
    """
    logger.info(f"User '{current_user.user_id}' is attempting to create topic '{topic_data.name}' for subject '{subject}'")

    try:
        # 1. Verify current_user is regent BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have current_user
        regent_info = await verify_regent_exists(current_user.user_id)

        # 2. Create the Topic in the local database
        db_topic = Topic(name=topic_data.name,subject_id=topic_data.subject_id)
        session.add(db_topic)
        await session.commit()
        await session.refresh(db_topic) # Get the auto-generated ID

        logger.info(f"Subject '{db_topic.name}' created in database with ID: {db_topic.id}")

        # Return success response
        return TopicCreateResponse(
            subject_id=db_topic.subject_id,
            name=db_topic.name,
            message="Topic created."
        )

    except ValueError as ve:
        # Handle specific validation errors like regent not found (caught by require_subject_regent)
        logger.warning(f"Validation error during topic creation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation (e.g., DB error, Keycloak error)
        logger.error(f"Failed to create topic '{topic_data.name}': {e}")
        logger.exception(e) # Log the full traceback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the topic in the database."
        )

# ... (keep existing endpoints like GET, PUT, etc.) ...

@router.get("/topic/{id}", response_model=TopicRead)
async def read_topic(
    id: int,
    session: AsyncSession = Depends(get_session)
    # session: AsyncSession = Depends(get_session) # Remove this dependency
):
    """Get topic info from provided id"""
    result = await session.get(Topic, id)
    if not result:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicRead.model_validate(result)
    
    