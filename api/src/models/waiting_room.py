from typing import Optional, List
from sqlmodel import Field, SQLModel
from pydantic import BaseModel
from enum import Enum
from sqlalchemy import Column, JSON

class WaitingRoomState(str, Enum):
    PREPARATION = "preparation"
    RUNNING = "running"
    CLOSED = "closed"
    FINISHED = "finished"

class WaitingRoom(SQLModel, table=True):
    __tablename__ = "waiting_room"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_config_id: int = Field(foreign_key="exam_config.id")
    state: WaitingRoomState = Field(default=WaitingRoomState.PREPARATION)
    associations: List[str] = Field(default=[], sa_column=Column(JSON))

class WaitingRoomCreateRequest(BaseModel):
    exam_config_id: int
    vigilant_keycloak_ids: List[str]

class WaitingRoomResponse(BaseModel):
    id: int
    exam_config_id: int
    state: WaitingRoomState
    associations: List[str]
    message: str
