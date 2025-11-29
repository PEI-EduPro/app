from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


class Topic(SQLModel, table=True):
    __tablename__ = "topic"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subject.id")
    name: str = Field(unique=True,index=True)
    
    # Relationships
    subject: "Subject" = Relationship(back_populates="topics")
    questions: List["Question"] = Relationship(back_populates="topic")
    exam_configs: List["ExamConfig"] = Relationship(back_populates="topic")

# Workbook schemas
class TopicCreate(SQLModel):
    """Schema for creating a newtopic"""
    name: str = Field(max_length=100)
    subject_id : int

class TopicUpdate(SQLModel):
    """Schema for updating workbook data"""
    name: Optional[str] = Field(default = None,max_length=100)

class TopicRead(SQLModel):
    """Schema for reading workbook data"""
    name: str
    subject_id: int

class TopicPublic(SQLModel):
    """Schema for public workbook data (limited info)"""
    id: int
    name: str
    subject_id : int

class TopicCreateRequest(SQLModel):
    """Schema for the request to create a topic via the API."""
    name: str
    subject_id: int

class TopicCreateResponse(SQLModel):
    """Schema for the response to create a topic via the API."""
    name: str
    subject_id: int



