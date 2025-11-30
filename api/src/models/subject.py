from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel

# --- Database Table ---
class Subject(SQLModel, table=True):
    __tablename__ = "subject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True,max_length=100)
    regent_keycloak_id: str
    topics: List["Topic"] = Relationship(back_populates="subject")

# SubjectUpdate for patch
class SubjectUpdate(SQLModel):
    name: Optional[str]
    regent_id: Optional[str]

# Used for POST /subject input
class SubjectCreateRequest(BaseModel):
    name: str
    regent_keycloak_id: str

class SubjectPublic(SQLModel):
    #id: int
    name: str
    regent_keycloak_id: str  # The Keycloak user ID of the professor to be made regent

