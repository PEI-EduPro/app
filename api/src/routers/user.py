import logging

from fastapi import APIRouter, HTTPException, status

from src.models.user import UserCreate, UserPublic
from src.core.keycloak import keycloak_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=UserPublic)
async def create_user_endpoint(
    user_data: UserCreate,
):
    """
    Create a new user in Keycloak.
    """
    try:
        return UserPublic.model_validate(user_data)
    except ValueError as ve:
        logger.warning(f"Failed to create user {user_data.username}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user in Keycloak."
        )
