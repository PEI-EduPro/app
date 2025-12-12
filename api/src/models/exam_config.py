# src/models/exam_config.py
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


# TopicConfig model - junction table between Topic and ExamConfig
class TopicConfig(SQLModel, table=True):
    __tablename__ = "topic_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id")
    exam_config_id: int = Field(foreign_key="exam_config.id")
    num_questions: int
    relative_weight: float = Field(default=1.0)
    
    # Relationships
    topic: "Topic" = Relationship(back_populates="topic_configs")
    exam_config: "ExamConfig" = Relationship(back_populates="topic_configs")


# ExamConfig model
class ExamConfig(SQLModel, table=True):
    __tablename__ = "exam_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    # creator_keycloak_id: str = Field(max_length=255)  # Commented out
    fraction: int = Field(default=0)
    subject_id: int = Field(foreign_key="subject.id")
    
    topic_configs: List["TopicConfig"] = Relationship(back_populates="exam_config",
                                                     sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    exams: List["Exam"] = Relationship(back_populates="exam_config")

# ExamConfig schemas
class ExamConfigCreate(SQLModel):
    """Schema for creating a new exam configuration"""
    # creator_keycloak_id: str  # Commented out
    fraction: int = 0
    subject_id: int

class ExamConfigUpdate(SQLModel):
    """Schema for updating exam configuration"""
    # creator_keycloak_id: Optional[str] = None  # Commented out
    fraction: Optional[int] = None
    subject_id: Optional[int] = None

class ExamConfigRead(SQLModel):
    """Schema for reading exam configuration data"""
    id: int
    # creator_keycloak_id: str  # Commented out
    fraction: int
    subject_id: int

class ExamConfigPublic(SQLModel):
    """Schema for public exam config data (limited info)"""
    id: int
    fraction: int
    subject_id: int