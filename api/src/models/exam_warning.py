from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


# Exam model
class ExamWarning(SQLModel, table=True):
    __tablename__ = "exam_warning"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exam.id")
    unfiltered_answers: str  = Field(default=None)
    
    # Relationships
    exam: "Exam" = Relationship(back_populates="exam_warnings")

# Exam schemas
class ExamWarningCreate(SQLModel):
    """Schema for creating a new exam"""
    exam_id: int
    unfiltered_answers: str

class ExamWarningUpdate(SQLModel):
    """Schema for updating exam data"""
    exam_id: int
    unfiltered_answers: str

class ExamWarningRead(SQLModel):
    """Schema for reading exam data"""
    exam_id: int
    unfiltered_answers: str

class ExamWarningPublic(SQLModel):
    """Schema for public exam data (no answers exposed)"""
    exam_id: int