from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


# Association tables for many-to-many relationships
class StudentSubjectLink(SQLModel, table=True):
    __tablename__ = "student_subject"
    
    student_id: int = Field(foreign_key="student.id", primary_key=True)
    subject_id: int = Field(foreign_key="subject.id", primary_key=True)

class ProfessorSubjectLink(SQLModel, table=True):
    __tablename__ = "professor_subject"
    
    professor_id: int = Field(foreign_key="professor.id", primary_key=True)
    subject_id: int = Field(foreign_key="subject.id", primary_key=True)

class Subject(SQLModel, table=True):
    __tablename__ = "subject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: str = Field(max_length=20, unique=True, index=True)
    name: str = Field(max_length=100)
    regent_id: Optional[int] = Field(default=None, foreign_key="professor.id")  # Professor appointed as regent by manager
    manager_id: Optional[int] = Field(default=None, foreign_key="manager.id")
    
    # Relationships
    manager: Optional["Manager"] = Relationship(back_populates="subjects_created")
    regent: Optional["Professor"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Subject.regent_id]"}
    )
    students: List["Student"] = Relationship(
        back_populates="subjects",
        link_model=StudentSubjectLink
    )
    professors: List["Professor"] = Relationship(
        back_populates="subjects",
        link_model=ProfessorSubjectLink
    )
    topics: List["Topic"] = Relationship(back_populates="subject")

class Topic(SQLModel, table=True):
    __tablename__ = "topic"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subject.id")
    
    # Relationships
    subject: "Subject" = Relationship(back_populates="topics")
    questions: List["Question"] = Relationship(back_populates="topic")
    exam_configs: List["ExamConfig"] = Relationship(back_populates="topic")

# Question model
class Question(SQLModel, table=True):
    __tablename__ = "question"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topic.id")
    question_text: str = Field(sa_column_kwargs={"type_": "TEXT"})
    
    # Relationships
    topic: "Topic" = Relationship(back_populates="questions")
    options: List["QuestionOption"] = Relationship(back_populates="question", cascade_delete=True)

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
