from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


# ExamConfig model
class ExamConfig(SQLModel, table=True):
    __tablename__ = "exam_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id")
    professor_id: int = Field(foreign_key="professor.id")
    num_questions: int
    fraction: int = Field(default=0)
    relative_weight: float = Field(default=1.0)
    
    # Relationships
    topic: "Topic" = Relationship(back_populates="exam_configs")
    professor: "Professor" = Relationship(back_populates="exam_configs")
    exams: List["Exam"] = Relationship(back_populates="exam_config")

# ExamConfig schemas
class ExamConfigCreate(SQLModel):
    """Schema for creating a new exam configuration"""
    topic_id: int
    professor_id: int
    num_questions: int
    fraction: int = 0
    relative_weight: float = 1.0

class ExamConfigUpdate(SQLModel):
    """Schema for updating exam configuration"""
    topic_id: Optional[int] = None
    professor_id: Optional[int] = None
    num_questions: Optional[int] = None
    fraction: Optional[int] = None
    relative_weight: Optional[float] = None

class ExamConfigRead(SQLModel):
    """Schema for reading exam configuration data"""
    id: int
    topic_id: int
    professor_id: int
    num_questions: int
    fraction: int
    relative_weight: float

class ExamConfigPublic(SQLModel):
    """Schema for public exam config data (limited info)"""
    id: int
    topic_id: int
    num_questions: int
    relative_weight: float


    

