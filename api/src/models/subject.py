from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


# Association tables for many-to-many relationships
class StudentSubjectLink(SQLModel, table=True):
    __tablename__ = "student_subject"
    
    student_id: int = Field(foreign_key="student.id", primary_key=True)
    subject_id: int = Field(foreign_key="subject.id", primary_key=True)

class ProfessorSubjectLink(SQLModel, table=True):
    __tablename__ = "professor_subject"
    
    professor_id: int = Field(foreign_key="professor.id", primary_key=True)
    subject_id: int = Field(foreign_key="subject.id", primary_key=True)

#SubjectModel
class Subject(SQLModel, table=True):
    __tablename__ = "subject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
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

#SubjectUpdate for patch
class SubjectUpdate(SQLModel):
    name: str | None = None
    regent_id: int | None = None
    manager_id: int | None = None

class SubjectCreate(SQLModel):
    name: str
    regent_id: int | None = None
    manager_id: int | None = None

class SubjectPublic(SQLModel):
    id: int
    name: str
