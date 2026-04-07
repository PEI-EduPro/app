from typing import Optional, List, Dict
from sqlmodel import Field, SQLModel
from pydantic import BaseModel
from enum import Enum
from sqlalchemy import Column, JSON

class WaitingRoomState(str, Enum):
    PREPARATION = "preparation"
    RUNNING = "running"
    CLOSED = "closed"

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

class StudentInfo(BaseModel):
    name: str
    nmec: str

class WaitingRoomInfoResponse(BaseModel):
    id: int
    subject_id: int
    subject_name: str
    exam_config_id: int
    state: WaitingRoomState
    associations: List[str]
    student_list: List[StudentInfo]
    exam_ids: List[int]
    total_students: int
    total_exams: int
    role: str

class WaitingRoomMetricsResponse(BaseModel):
    associated_exams_count: int
    associated_students_count: int


class ProfessorWaitingRoomItem(BaseModel):
    """Information about a single waiting room for a professor."""
    subject_id: int
    subject_name: str
    waiting_room_id: int
    state: str
    role: str
    exam_name: Optional[str]


class QRCodeToNMEC(BaseModel):
    qr: str
    nmec: int
