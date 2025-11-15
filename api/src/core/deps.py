import asyncio
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.db import get_session
from src.core.keycloak import keycloak_client
from src.services.user import get_user_by_keycloak_id, create_user
from src.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
):
    """Dependency to get current user from Keycloak token"""

    # TEMPORARY: For testing only - remove in production!
    #Para testar no Swagger clicar em authorize e inserir "test"
    if credentials.credentials == "test":
        user = await get_user_by_keycloak_id(session, "test-user-id")
        if not user:
            user = await create_user(
                session=session,
                keycloak_id="test-user-id",
                email="test@example.com",
                name="Test User",
                mechanographic_number="696969"
            )
        return user


    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verify the token with Keycloak
    token_info = await keycloak_client.verify_token(credentials.credentials)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Get or create user in our database
    keycloak_id = token_info.get("sub")
    email = token_info.get("email")
    name = token_info.get("name", token_info.get("preferred_username", ""))
    
    user = await get_user_by_keycloak_id(session, keycloak_id)
    if not user:
        user = await create_user(
            session=session,
            keycloak_id=keycloak_id,
            email=email,
            name=name,
            mechanographic_number=None
        )
    
    return user

def require_role(role: str):
    """Dependency factory to require specific role"""
    async def role_dependency(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {role} role"
            )
        return current_user
    return role_dependency

# Role-specific dependencies
require_manager = require_role("manager")
require_professor = require_role("professor") 
require_student = require_role("student")