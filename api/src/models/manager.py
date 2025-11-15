from typing import Optional, List
from .subject import ProfessorSubjectLink, StudentSubjectLink
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum



class Manager(SQLModel, table=True):
    __tablename__ = "manager"
    
    id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    name: str = Field(index=True)
    
    subjects_created: List["Subject"] = Relationship(back_populates="manager")

# Manager schemas
class ManagerCreate(SQLModel):
    """Schema for creating a new manager"""
    name: str = Field(max_length=100)
    email: str = Field(max_length=100)

class ManagerUpdate(SQLModel):
    """Schema for updating manager data"""
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)

class ManagerRead(SQLModel):
    """Schema for reading manager data"""
    id: int
    name: str
    email: str
    user_type: str

class ManagerPublic(SQLModel):
    """Schema for public manager data (limited info)"""
    id: int
    name: str