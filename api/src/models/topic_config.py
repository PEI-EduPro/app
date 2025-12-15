# src/models/topic_config.py
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


# TopicConfig model
class TopicConfig(SQLModel, table=True):
    __tablename__ = "topic_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id")
    exam_config_id: int = Field(foreign_key="exam_config.id")
    #creator_keycloak_id: str = Field(max_length=255)
    num_questions: int
    relative_weight: float = Field(default=1.0)
    
    # Relationships
    topic: "Topic" = Relationship(back_populates="topic_configs")
    exam_config: "ExamConfig" = Relationship(back_populates="topic_configs")

# DTOs
class TopicConfigDTO(SQLModel):
    id: int
    topic_id: int
    topic_name: str
    num_questions: int
    relative_weight: float