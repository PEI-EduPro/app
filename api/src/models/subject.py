from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class Subject(SQLModel, table=True):
    __tablename__ = "subject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    topics: List["Topic"] = Relationship(back_populates="subject")

# SubjectUpdate for patch
class SubjectUpdate(SQLModel):
    name: str | None = None

class SubjectCreate(SQLModel):
    name: str

class SubjectPublic(SQLModel):
    id: int
    name: str