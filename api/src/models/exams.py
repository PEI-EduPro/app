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
    penalty: float = Field(default=0.0)
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
    penalty: float = 0.0
    relative_weight: float = 1.0

class ExamConfigUpdate(SQLModel):
    """Schema for updating exam configuration"""
    topic_id: Optional[int] = None
    professor_id: Optional[int] = None
    num_questions: Optional[int] = None
    penalty: Optional[float] = None
    relative_weight: Optional[float] = None

class ExamConfigRead(SQLModel):
    """Schema for reading exam configuration data"""
    id: int
    topic_id: int
    professor_id: int
    num_questions: int
    penalty: float
    relative_weight: float

class ExamConfigPublic(SQLModel):
    """Schema for public exam config data (limited info)"""
    id: int
    topic_id: int
    num_questions: int
    relative_weight: float


# Exam model
class Exam(SQLModel, table=True):
    __tablename__ = "exam"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    exam_config_id: int = Field(foreign_key="exam_config.id")
    exam_xml: Optional[str] = Field(default=None)
    
    # Relationships
    exam_config: "ExamConfig" = Relationship(back_populates="exams")

# Exam schemas
class ExamCreate(SQLModel):
    """Schema for creating a new exam"""
    question_id: int
    exam_config_id: int
    exam_xml: Optional[str] = None

class ExamUpdate(SQLModel):
    """Schema for updating exam data"""
    question_id: Optional[int] = None
    exam_config_id: Optional[int] = None
    exam_xml: Optional[str] = None

class ExamRead(SQLModel):
    """Schema for reading exam data"""
    id: int
    question_id: int
    exam_config_id: int
    exam_xml: Optional[str] = None

class ExamPublic(SQLModel):
    """Schema for public exam data (no answers exposed)"""
    id: int
    exam_config_id: int

    

