import logging

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.deps import get_current_user_info, require_manager
from src.models.user import UserCreate, User, UserPublic
from src.core.keycloak import keycloak_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/me", response_model=UserPublic)
async def read_current_user(
    user: User = Depends(get_current_user_info)
):
    """Get current user info from the token (requires authentication)"""
    return UserPublic.model_validate(user)

@router.post("/create", response_model=UserPublic) #, dependencies=[Depends(require_manager)])
async def create_user_endpoint(
    user_data: UserCreate,
    current_user_info: User = Depends(get_current_user_info) # Ensures authentication
):
    """
    Create a new user in Keycloak (Manager only).
    """
    # Explicitly check for manager role here if you want to avoid the dependency on the router level
    if "manager" not in current_user_info.realm_roles:
         raise HTTPException(status_code=403, detail="Requires manager role")

    logger.info(f"Manager {current_user_info.username} is attempting to create a new user: {user_data.username}")
    try:
        # Call the method in keycloak.py
        result = await keycloak_client.create_user_in_keycloak(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            temporary=user_data.temporary_password,
            realm_role=user_data.realm_role, # Pass the role to assign
            nmec=user_data.nmec
        )
        logger.info(f"User {user_data.username} created successfully by manager {current_user_info.username}.")
        
        # Create a dict from user_data and add the user_id from Keycloak result
        response_data = user_data.model_dump()
        response_data["user_id"] = result["user_id"]
        
        return UserPublic.model_validate(response_data)
    except ValueError as ve:
        # Handle specific validation errors like user exists
        logger.warning(f"Failed to create user {user_data.username}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation
        logger.error(f"Failed to create user {user_data.username} by manager {current_user_info.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user in Keycloak."
        )

@router.get("/debug/token-info")
async def debug_token_info(
    user_info: User = Depends(get_current_user_info),
    _ = Depends(require_manager) # Only accessible by managers for debugging
):
    """Debug endpoint to see the full decoded token info (managers only)"""
    return user_info