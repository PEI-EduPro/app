import logging

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.deps import get_current_user_info, require_manager # Import require_manager
from src.models.user import UserCreateRequest, CurrentUserInfo, UserCreateResponse,User # Import the schema
from src.core.keycloak import keycloak_client # Import the keycloak client instance

logger = logging.getLogger(__name__)

router = APIRouter()



@router.get("/me", response_model=CurrentUserInfo)
async def read_current_user(
    user: User = Depends(get_current_user_info)
    # session: AsyncSession = Depends(get_session) # Remove this dependency
):
    """Get current user info from the token (requires authentication)"""
    # You could still apply a role check here if desired, e.g., only allow certain roles to access this endpoint
    # await require_manager(user_info) # Uncomment if only managers should access /me
    return CurrentUserInfo.model_validate(user)


@router.post("/create", response_model=UserCreateResponse, dependencies=[Depends(require_manager)])
async def create_user_endpoint(
    user_data: UserCreateRequest,
    current_user_info: User = Depends(get_current_user_info) # This will be the manager's info due to require_manager
):
    """
    Create a new user in Keycloak (Manager only).
    Requires the 'manager' role.
    """
    logger.info(f"Manager {current_user_info['username']} is attempting to create a new user: {user_data.username}")

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
        logger.info(f"User {user_data.username} created successfully by manager {current_user_info['username']}.")
        return UserCreateResponse(
            user_id=result["user_id"],
            message=result["message"]
        )
    except ValueError as ve:
        # Handle specific validation errors like user exists
        logger.warning(f"Failed to create user {user_data.username}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation
        logger.error(f"Failed to create user {user_data.username} by manager {current_user_info['username']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user in Keycloak."
        )


# The update_user_role_endpoint is removed as roles are managed in Keycloak
# @router.put("/{user_id}/role", response_model=UserRead)
# async def update_user_role_endpoint(...):
#     # This functionality is moved to Keycloak admin console
#     pass

# Add a debug endpoint if needed (maybe for managers only)
@router.get("/debug/token-info")
async def debug_token_info(
    user_info: User = Depends(get_current_user_info),
    _ = Depends(require_manager) # Only accessible by managers for debugging
):
    """Debug endpoint to see the full decoded token info (managers only)"""
    return user_info
