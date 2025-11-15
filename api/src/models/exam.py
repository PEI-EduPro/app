from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


# Exam model
class Exam(SQLModel, table=True):
    __tablename__ = "exam"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_config_id: int = Field(foreign_key="exam_config.id")
    exam_xml: Optional[str] = Field(default=None, sa_column_kwargs={"type_": "TEXT"})
    
    # Relationships
    exam_config: "ExamConfig" = Relationship(back_populates="exams")

# Exam schemas
class ExamCreate(SQLModel):
    """Schema for creating a new exam"""
    exam_config_id: int
    exam_xml: Optional[str] = None

class ExamUpdate(SQLModel):
    """Schema for updating exam data"""
    exam_config_id: Optional[int] = None
    exam_xml: Optional[str] = None

class ExamRead(SQLModel):
    """Schema for reading exam data"""
    id: int
    exam_config_id: int
    exam_xml: Optional[str] = None

class ExamPublic(SQLModel):
    """Schema for public exam data (no answers exposed)"""
    id: int
    exam_config_id: int

    

