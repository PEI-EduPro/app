# src/schemas/subject.py
from pydantic import BaseModel
from typing import Optional

class SubjectCreateRequest(BaseModel):
    name: str
    regent_keycloak_id: str  # The Keycloak user ID of the professor to be made regent

class SubjectCreateResponse(BaseModel):
    id: int
    name: str
    message: str
    regent_username: str # Optional: Return the regent's username for confirmation