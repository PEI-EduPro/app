from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

# QuestionOption model - allows multiple options
class QuestionOption(SQLModel, table=True):
    __tablename__ = "question_option"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id", ondelete="CASCADE")
    option_text: str = Field(max_length=500)
    
    # Relationships
    question: "Question" = Relationship(back_populates="options")

# QuestionOption schemas
class QuestionOptionCreate(SQLModel):
    """Schema for creating a new question option"""
    option_text: str = Field(max_length=500)

class QuestionOptionUpdate(SQLModel):
    """Schema for updating question option data"""
    option_text: Optional[str] = Field(default=None, max_length=500)

class QuestionOptionRead(SQLModel):
    """Schema for reading question option data"""
    id: int
    question_id: int
    option_text: str

class QuestionOptionPublic(SQLModel):
    """Schema for public question option data"""
    id: int
    question_id: int
    option_text: str

class QuestionOptionDelete(SQLModel):
    """Schema for deleting a question option"""
    id: int
