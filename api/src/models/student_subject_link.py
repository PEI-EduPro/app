from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


# Association tables for many-to-many relationships
class StudentSubjectLink(SQLModel, table=True):
    __tablename__ = "student_subject"
    
    student_id: int = Field(foreign_key="student.id", primary_key=True)
    subject_id: int = Field(foreign_key="subject.id", primary_key=True)

# StudentSubjectLink schemas
class StudentSubjectLinkCreate(SQLModel):
    """Schema for creating a student-subject link"""
    student_id: int
    subject_id: int

class StudentSubjectLinkRead(SQLModel):
    """Schema for reading student-subject link data"""
    student_id: int
    subject_id: int

class StudentSubjectLinkPublic(SQLModel):
    """Schema for public student-subject link data"""
    student_id: int
    subject_id: int

class StudentSubjectLinkDelete(SQLModel):
    """Schema for deleting a student-subject link"""
    student_id: int
    subject_id: int