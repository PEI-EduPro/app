from typing import Optional
from sqlmodel import SQLModel

class User(SQLModel):
    """Base model for user"""
    user_id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    #temporary_password: Optional[str] = None
    #realm_roles: Optional[list[str]] = None
    #nmec: Optional[str] = None
    #groups: Optional[list[str]] = None

class UserCreate(SQLModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    #temporary_password: Optional[str] = None
    #realm_roles: Optional[str] = None
    #nmec: Optional[str] = None


class UserPublic(SQLModel):
    #user_id: str # Keycloak user ID
    username: str
    email: str
    #realm_roles: list[str]
    #groups: list[str]

