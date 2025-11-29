import asyncio
import logging
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
from src.core.settings import settings
from src.core.keycloak import keycloak_client
from src.models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user info from Keycloak token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = credentials.credentials
    # Verify token and get user info from Keycloak
    token_info = await keycloak_client.verify_token(token) # Your existing verify_token function
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Extract key information
    user_id = token_info.get("sub")
    username = token_info.get("preferred_username")
    email = token_info.get("email")
    realm_roles = token_info.get("realm_access", {}).get("roles", [])
    groups = token_info.get("groups", []) # Groups are typically here in the token

    # Optional: Fetch more details from userinfo endpoint if needed
    # user_info = await keycloak_client.get_userinfo(token) # Add this method if needed
    # groups = user_info.get("groups", groups) # Fallback or additional check

    logger.info(f"Authenticated user: {username}, roles: {realm_roles}, groups: {groups}")
    user = User(user_id=user_id,username=username,email=email,realm_roles=realm_roles,groups=groups)

    return user
    

def require_role(role_name: str):
    """Dependency factory to require a specific realm role"""
    async def role_check(user_info: dict = Depends(get_current_user_info)):
        if role_name not in user_info.get("realm_roles", []):
            logger.warning(f"User {user_info['username']} lacks required role: {role_name}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {role_name} role"
            )
        logger.info(f"User {user_info['username']} has required role: {role_name}")
        return user_info
    return role_check

def require_group(group_name: str):
    """Dependency factory to require a specific group membership"""
    async def group_check(user_info: dict = Depends(get_current_user_info)):
        if group_name not in user_info.get("groups", []):
            logger.warning(f"User {user_info['username']} is not in required group: {group_name}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires membership in group {group_name}"
            )
        logger.info(f"User {user_info['username']} is in required group: {group_name}")
        return user_info
    return group_check

# Define specific dependencies based on your roles/groups
require_manager = require_role("manager")
require_professor = require_role("professor")
require_student = require_role("student")

def require_subject_regent(subject_id: str):
    group_name = f"/s{subject_id}/regent"
    return require_group(group_name)

def require_subject_student(subject_id: str):
    group_name = f"/s{subject_id}/student"
    return require_group(group_name)

def require_edit_question_bank(subject_id: str):
    group_name = f"/s{subject_id}/edit_question_bank"
    return require_group(group_name)


async def verify_regent_exists(regent_keycloak_id: str):
    """Dependency to check if the regent user exists in Keycloak before proceeding."""
    try:
        # Run the synchronous keycloak operation in a thread pool
        loop = asyncio.get_event_loop()
        regent_info = await loop.run_in_executor(
            None, # Uses default executor (ThreadPoolExecutor)
            lambda: keycloak_client.admin_client.get_user(regent_keycloak_id) # Wrap the sync call
        )
        logger.info(f"Verified regent user exists: {regent_info.get('username')} (ID: {regent_keycloak_id})")
        return regent_info # Return user info if needed later
    except Exception as e:
        logger.error(f"Failed to verify regent user {regent_keycloak_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Regent user with ID '{regent_keycloak_id}' not found in Keycloak."
        )
        # Or raise a ValueError to be caught by the endpoint handler
        # raise ValueError(f"Regent user with ID '{regent_keycloak_id}' not found.")