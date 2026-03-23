# src/models/exam_config.py
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from src.models.topic_config import TopicConfigDTO


# ExamConfig model
class ExamConfig(SQLModel, table=True):
    __tablename__ = "exam_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    #creator_keycloak_id: str = Field(max_length=255)
    fraction: int = Field(default=0)
    subject_id: int = Field(foreign_key="subject.id")
    nmec_name_list: Optional[str] # nmec (string): {name: string, email: string}
    
    topic_configs: List["TopicConfig"] = Relationship(back_populates="exam_config",
                                                     sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    exams: List["Exam"] = Relationship(back_populates="exam_config")

# ExamConfig schemas
class ExamConfigCreate(SQLModel):
    """Schema for creating a new exam configuration"""
    # creator_keycloak_id: str  # Commented out
    fraction: int = 0
    subject_id: int
    nmec_list: Optional[str] #dict{nmec : nome}

class ExamConfigUpdate(SQLModel):
    """Schema for updating exam configuration"""
    # creator_keycloak_id: Optional[str] = None  # Commented out
    fraction: Optional[int] = None
    subject_id: Optional[int] = None
    nmec_list: Optional[str] #dict{nmec : nome}

class ExamConfigRead(SQLModel):
    """Schema for reading exam configuration data"""
    id: int
    # creator_keycloak_id: str  # Commented out
    fraction: int
    subject_id: int
    

class ExamConfigResponse(SQLModel):
    id: int
    subject_id: int
    fraction: int
    #creator_keycloak_id: str
    topic_configs: List[TopicConfigDTO]
    nmec_name_list: Optional[str]
