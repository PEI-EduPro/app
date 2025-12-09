from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel

# --- Database Table ---
class Subject(SQLModel, table=True):
    __tablename__ = "subject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True,max_length=100)
    # The topic relationship uses a string forward reference to avoid circular imports
    topics: List["Topic"] = Relationship(
        back_populates="subject",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"} 
    )

# --- Pydantic DTOs (Request/Response Schemas) ---

# Used for POST /subject input
class SubjectCreateRequest(BaseModel):
    name: str

# Used for POST /subject output
class SubjectCreateResponse(BaseModel):
    id: int
    name: str

# Used for GET /subject output
class SubjectRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# Used for the patch/put
class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    regent_keycloak_id: Optional[str] = None

# --- Student DTOs ---

class StudentAddRequest(BaseModel):
    student_keycloak_ids: List[str]

class StudentInfo(BaseModel):
    id: str   # This is the keycloak id
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# --- Professor Permission DTOs ---

class ProfessorPermissions(BaseModel):
    """Base class defining the specific boolean permissions"""
    edit_topics: bool = False
    edit_questions: bool = False
    view_question_bank: bool = False
    add_students: bool = False
    generate_exams: bool = False
    view_grades: bool = False
    auto_correct_exams: bool = False

class ProfessorAddRequest(ProfessorPermissions):
    """Used for POST /subject/{id}/professors"""
    professor_keycloak_id: str

class ProfessorUpdateRequest(ProfessorPermissions):
    """Used for PUT /subject/{id}/professors/{user_id}"""
    pass # Inherits all boolean fields