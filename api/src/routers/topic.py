# src/routers/topic.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.services import topic
from src.services import question
from src.core.db import get_session
from src.core.deps import get_current_user_info, verify_permission
from src.models.topic import TopicCreate, TopicPublic
from src.models.common import MessageResponse
from src.models.user import User
import logging


logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=TopicPublic)
async def create_topic(
    topic_data: TopicCreate,
    session: AsyncSession = Depends(get_session),
    user_info: User = Depends(get_current_user_info)
):
    """
    Create a new topic in the database.
    Requires the 'edit_topics' group permission.
    """
    verify_permission(user_info, [f"/s{topic_data.subject_id}/edit_topics", f"/s{topic_data.subject_id}/regent"])
    try:
        db_topic = await topic.create_topic(session,topic_data)

        logger.info(f"Topic '{db_topic.name}' created in database with ID: {db_topic.id}")

        # Return success response
        return TopicPublic.model_validate(db_topic)

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

@router.get("/{id}", response_model=TopicPublic)
async def read_topic(
    id: int,
    session: AsyncSession = Depends(get_session),
    user_info: User = Depends(get_current_user_info)
):
    """Get topic info from provided name"""
    result = await topic.get_topic_by_id(session,id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    verify_permission(user_info, [f"/s{result.subject_id}"])
    return TopicPublic.model_validate(result)

@router.put("/{id}", response_model=TopicPublic)
async def update_topic(
    id: int,
    topic_data: topic.TopicUpdate,
    session: AsyncSession = Depends(get_session),
    user_info: User = Depends(get_current_user_info)
):
    """Update topic"""
    existing_topic = await topic.get_topic_by_id(session, id)
    if not existing_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    verify_permission(user_info, [f"/s{existing_topic.subject_id}/edit_topics", f"/s{existing_topic.subject_id}/regent"])
    return await topic.update_topic(session, topic_data, id)

@router.delete("/{id}", response_model=MessageResponse)
async def delete_topic(
    id: int,
    session: AsyncSession = Depends(get_session),
    user_info: User = Depends(get_current_user_info)
):
    """Delete topic"""
    existing_topic = await topic.get_topic_by_id(session, id)
    if not existing_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    verify_permission(user_info, [f"/s{existing_topic.subject_id}/edit_topics", f"/s{existing_topic.subject_id}/regent"])
    if await topic.delete_topic(session, id):
        return {"message": "Topic deleted successfully"}
    raise HTTPException(status_code=404, detail="Topic not found")