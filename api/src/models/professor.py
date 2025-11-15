from typing import Optional, List
from .subject import ProfessorSubjectLink, StudentSubjectLink
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum



class Professor(SQLModel, table=True):
    __tablename__ = "professor"
    
    id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    name: str = Field(index=True)
    
    subjects: List["Subject"] = Relationship(
        back_populates="professors",
        link_model=ProfessorSubjectLink
    )
    workbooks: List["Workbook"] = Relationship(back_populates="professor")
    exam_configs: List["ExamConfig"] = Relationship(back_populates="professor")

# Professor schemas
class ProfessorCreate(SQLModel):
    """Schema for creating a new professor"""
    name: str = Field(max_length=100)
    email: str = Field(max_length=100)

class ProfessorUpdate(SQLModel):
    """Schema for updating professor data"""
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)

class ProfessorRead(SQLModel):
    """Schema for reading professor data"""
    id: int
    name: str
    email: str

class ProfessorPublic(SQLModel):
    """Schema for public professor data (limited info)"""
    id: int
    name: str


