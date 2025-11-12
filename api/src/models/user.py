from sqlmodel import Field, SQLModel
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    MANAGER = "manager"
    PROFESSOR = "professor"
    STUDENT = "student"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    keycloak_id: str = Field(unique=True, index=True)
    mechanographic_number: Optional[str] = Field(default=None, unique=True, index=True)
    email: str = Field(unique=True, index=True)
    name: str
    role: UserRole = Field(default=UserRole.STUDENT)
    is_active: bool = Field(default=True)

class UserCreate(SQLModel):
    keycloak_id: str
    email: str
    name: str
    mechanographic_number: Optional[str] = None
    role: UserRole = UserRole.STUDENT

class UserRead(SQLModel):
    id: int
    email: str
    name: str
    mechanographic_number: Optional[str]
    role: UserRole
    is_active: bool