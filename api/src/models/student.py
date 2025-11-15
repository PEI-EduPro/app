from typing import Optional, List
from .subject import ProfessorSubjectLink, StudentSubjectLink
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

    

class Student(SQLModel, table=True):
    __tablename__ = "student"
    
    id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True,index=True)

    subjects: List["Subject"] = Relationship(
        back_populates="students",
        link_model=StudentSubjectLink
    )

# Student schemas
class StudentCreate(SQLModel):
    """Schema for creating a new student"""
    name: str = Field(max_length=100)
    email: str = Field(max_length=100)

class StudentUpdate(SQLModel):
    """Schema for updating student data"""
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)

class StudentRead(SQLModel):
    """Schema for reading student data"""
    id: int
    name: str
    email: str

class StudentPublic(SQLModel):
    """Schema for public student data (limited info)"""
    id: int
    name: str
    email: str
