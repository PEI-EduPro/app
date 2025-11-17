from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum




class Topic(SQLModel, table=True):
    __tablename__ = "topic"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subject.id")
    name: str = Field(index=True)
    
    # Relationships
    subject: "Subject" = Relationship(back_populates="topics")
    questions: List["Question"] = Relationship(back_populates="topic")


class TopicCreate(SQLModel):
    subject_id: int
    name: str


class TopicRead(SQLModel):
    id: int
    subject_id: int
    name: str