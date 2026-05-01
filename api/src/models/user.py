from typing import Optional, List
from sqlmodel import SQLModel

class User(SQLModel):
    """
    Base model for user. 
    Used by dependency injection (deps.py) to pass user context.
    """
    user_id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # These fields are required by your Service Layer (subject.py and deps.py)
    # They must NOT be commented out.
    realm_roles: List[str] = []
    groups: List[str] = []
    
    nmec: Optional[str] = None

class UserCreate(SQLModel):
    """Used for creating a new user (if applicable)"""
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    temporary_password: bool = False
    realm_role: Optional[str] = None 
    nmec: Optional[str] = None

class UserPublic(SQLModel):
    """Used for returning user info to frontend"""
    user_id: str
    username: str
    email: str
    realm_roles: List[str] = []
    groups: List[str] = []


class KeycloakUserPublic(SQLModel):
    """Used for returning Keycloak user listings (professors/students)"""
    id: str
    username: Optional[str] = None
    email: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
