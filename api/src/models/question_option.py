from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum




# QuestionOption model - allows multiple options with fractional scoring
class QuestionOption(SQLModel, table=True):
    __tablename__ = "question_option"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id", ondelete="CASCADE")
    option_text: str = Field(max_length=500)
    fraction: float = Field(default=0.0)  # 100.0 for correct, negative for incorrect (based on penalty)
    order_position: Optional[int] = Field(default=None)  # For displaying options in specific order
    
    # Relationships
    question: "Question" = Relationship(back_populates="options")

# QuestionOption schemas
class QuestionOptionCreate(SQLModel):
    """Schema for creating a new question option"""
    question_id: int
    option_text: str = Field(max_length=500)
    fraction: float = 0.0
    order_position: Optional[int] = None

class QuestionOptionUpdate(SQLModel):
    """Schema for updating question option data"""
    option_text: Optional[str] = Field(default=None, max_length=500)
    fraction: Optional[float] = None
    order_position: Optional[int] = None

class QuestionOptionRead(SQLModel):
    """Schema for reading question option data"""
    id: int
    question_id: int
    option_text: str
    fraction: float
    order_position: Optional[int] = None

class QuestionOptionPublic(SQLModel):
    """Schema for public question option data (no fraction exposed)"""
    id: int
    question_id: int
    option_text: str
    order_position: Optional[int] = None

class QuestionOptionDelete(SQLModel):
    """Schema for deleting a question option"""
    id: int
