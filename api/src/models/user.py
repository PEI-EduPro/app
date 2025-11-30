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
    
    # Optional fields that might be useful later
    password: Optional[str] = None
    nmec: Optional[str] = None

class UserCreate(SQLModel):
    """Used for creating a new user (if applicable)"""
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    # temporary_password: Optional[str] = None
    realm_roles: Optional[str] = None # Assuming this comes as a string from frontend forms
    nmec: Optional[str] = None

class UserPublic(SQLModel):
    """Used for returning user info to frontend"""
    user_id: str
    username: str
    email: str
    realm_roles: List[str] = []
    groups: List[str] = []