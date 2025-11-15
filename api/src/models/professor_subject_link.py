from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

class ProfessorSubjectLink(SQLModel, table=True):
    __tablename__ = "professor_subject"
    
    professor_id: int = Field(foreign_key="professor.id", primary_key=True)
    subject_id: int = Field(foreign_key="subject.id", primary_key=True)

# ProfessorSubjectLink schemas
class ProfessorSubjectLinkCreate(SQLModel):
    """Schema for creating a professor-subject link"""
    professor_id: int
    subject_id: int

class ProfessorSubjectLinkRead(SQLModel):
    """Schema for reading professor-subject link data"""
    professor_id: int
    subject_id: int

class ProfessorSubjectLinkPublic(SQLModel):
    """Schema for public professor-subject link data"""
    professor_id: int
    subject_id: int

class ProfessorSubjectLinkDelete(SQLModel):
    """Schema for deleting a professor-subject link"""
    professor_id: int
    subject_id: int