# src/models/exam_config.py
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


# TopicConfig model
class TopicConfig(SQLModel, table=True):
    __tablename__ = "topic_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id")
    exam_config_id: int = Field(foreign_key="exam_config.id")
    creator_keycloak_id: str = Field(max_length=255)
    num_questions: int
    relative_weight: float = Field(default=1.0)
    
    # Relationships
    topic: "Topic" = Relationship(back_populates="topic_configs")
    exam_config: "ExamConfig" = Relationship(back_populates="topic_configs")

# ExamConfig schemas
class ExamConfigCreate(SQLModel):
    """Schema for creating a new exam configuration"""
    topic_id: int
    creator_keycloak_id: str  # Use Keycloak ID instead of local professor ID
    num_questions: int
    fraction: int = 0
    relative_weight: float = 1.0

class ExamConfigUpdate(SQLModel):
    """Schema for updating exam configuration"""
    topic_id: Optional[int] = None
    creator_keycloak_id: Optional[str] = None  # Use Keycloak ID instead of local professor ID
    num_questions: Optional[int] = None
    fraction: Optional[int] = None
    relative_weight: Optional[float] = None

class ExamConfigRead(SQLModel):
    """Schema for reading exam configuration data"""
    id: int
    topic_id: int
    creator_keycloak_id: str  # Use Keycloak ID instead of local professor ID
    num_questions: int
    fraction: int
    relative_weight: float

class ExamConfigPublic(SQLModel):
    """Schema for public exam config data (limited info)"""
    id: int
    topic_id: int
    # Potentially remove creator_keycloak_id from public schema if not needed
    # creator_keycloak_id: str
    num_questions: int
    relative_weight: float