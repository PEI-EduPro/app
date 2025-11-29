from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel

# --- Database Table ---
class Subject(SQLModel, table=True):
    __tablename__ = "subject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    # Ensure "Topic" is in quotes to handle forward reference
    topics: List["Topic"] = Relationship(back_populates="subject")

# --- Pydantic DTOs (Request/Response Schemas) ---

# Used for POST /subject input
class SubjectCreateRequest(BaseModel):
    name: str
    regent_keycloak_id: str  # The Keycloak user ID of the professor to be made regent

# Used for POST /subject output
class SubjectCreateResponse(BaseModel):
    id: int
    name: str
    message: str
    regent_username: str | None = None

# Used for GET /subject output
class SubjectRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# Used for the patch
class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    regent_keycloak_id: Optional[str] = None

 # Adding a student to a subject
class StudentAddRequest(BaseModel):
    student_keycloak_ids: List[str]

# View student information
class StudentInfo(BaseModel):
    id: str   # This is the keycloak id
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

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
