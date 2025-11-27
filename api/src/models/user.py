from typing import Optional
from sqlmodel import SQLModel

class User(SQLModel):
    """Base model for user"""
    user_id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    temporary_password: Optional[str] = None
    realm_role: Optional[list[str]] = None
    nmec: Optional[str] = None
    groups: Optional[list[str]] = None

class UserCreate(SQLModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    temporary_password: str
    realm_role: str
    nmec: Optional[str] = None

class UserCreateRequest(SQLModel):
    """Schema for the request to create a user via the API."""
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: str
    temporary_password: bool = False  # Whether the user must change password on next login
    realm_role: Optional[str] = None  # e.g., 'student', 'professor', 'manager'. Must be an existing realm role in Keycloak.
    nmec: Optional[str] = None

    class Config:
        # Allow extra fields in case Keycloak supports more attributes in the future
        extra = "allow"

class CurrentUserInfo(SQLModel):
    id: str # Keycloak user ID
    username: str
    email: str
    realm_roles: list[str]
    groups: list[str]

class UserCreateResponse(SQLModel):
    user_id: str
    message: str