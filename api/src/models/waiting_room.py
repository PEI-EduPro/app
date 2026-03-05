from typing import Optional, List
from sqlmodel import Field, SQLModel
from pydantic import BaseModel

class WaitingRoom(SQLModel, table=True):
    __tablename__ = "waiting_room"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_config_id: int = Field(foreign_key="exam_config.id")

class WaitingRoomCreateRequest(BaseModel):
    exam_config_id: int
    vigilant_keycloak_ids: List[str]

class WaitingRoomResponse(BaseModel):
    id: int
    exam_config_id: int
    message: str
