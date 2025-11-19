# src/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreateRequest(BaseModel):
    """Schema for the request to create a user via the API."""
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: str
    temporary_password: bool = False  # Whether the user must change password on next login
    realm_role: Optional[str] = None  # e.g., 'student', 'professor', 'manager'. Must be an existing realm role in Keycloak.
    # Add other fields as needed, e.g., for mechanographic number if stored in Keycloak attributes

    class Config:
        # Allow extra fields in case Keycloak supports more attributes in the future
        extra = "allow"