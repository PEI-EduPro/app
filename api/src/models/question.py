from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

# Question model
class Question(SQLModel, table=True):
    __tablename__ = "question"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id")
    question_text: str = Field(default="Empty Question")
    
    # Relationships
    topic: "Topic" = Relationship(back_populates="questions")
    question_options: List["QuestionOption"] = Relationship(
        back_populates="question",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

# Question schemas
class QuestionCreate(SQLModel):
    """Schema for creating a new question"""
    topic_id: int
    question_text: str = "Empty Question"

class QuestionUpdate(SQLModel):
    """Schema for updating question data"""
    id: int
    topic_id: Optional[int] = None
    question_text: Optional[str] = None


class QuestionPublic(SQLModel):
    """Schema for public question data"""
    id: int
    topic_id: int
    question_text: str

class QuestionDelete(SQLModel):
    """Schema for deleting a question"""
    id: int

