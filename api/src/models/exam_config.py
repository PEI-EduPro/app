# src/models/exam_config.py
from typing import Optional, List, Dict, Tuple
from sqlmodel import Field, SQLModel, Relationship
from src.models.topic_config import TopicConfigDTO
from pydantic import BaseModel
from sqlalchemy import Column, JSON


from enum import Enum

class GenerationStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ExamState(str, Enum):
    PREPARING = "preparing"
    RUNNING = "running"
    CLOSED_AND_CAPTURE = "closed_and_capture"
    WARNING_HANDLING = "warning_handling"
    VALIDATION = "validation"
    COMPLETED = "completed"

# ExamConfig model
class ExamConfig(SQLModel, table=True):
    __tablename__ = "exam_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    fraction: int = Field(default=0)
    subject_id: int = Field(foreign_key="subject.id")
    nmec_name_list: Optional[str] = None # nmec (string): {name: string, email: string}
    exam_name: Optional[str] = Field(default=None, max_length=255)
    num_versions: int = Field(default=1)
    status: GenerationStatus = Field(default=GenerationStatus.PENDING)
    zip_path: Optional[str] = Field(default=None)
    
    # Merged from WaitingRoom
    state: ExamState = Field(default=ExamState.PREPARING)
    associations: List[str] = Field(default=[], sa_column=Column(JSON))

    topic_configs: List["TopicConfig"] = Relationship(back_populates="exam_config",
                                                     sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    exams: List["Exam"] = Relationship(back_populates="exam_config")

    @property
    def total_exams(self) -> int:
        """Count of generated exams for this configuration."""
        try:
            return len(self.exams) if self.exams is not None else 0
        except Exception:
            return 0

    @property
    def associated_exams_count(self) -> Optional[int]:
        """Count of exams that have been associated with a student."""
        if self.state not in [ExamState.RUNNING, ExamState.CLOSED_AND_CAPTURE, ExamState.WARNING_HANDLING, ExamState.VALIDATION, ExamState.COMPLETED]:
            return None
        try:
            return sum(1 for e in self.exams if e.nmec is not None) if self.exams is not None else 0
        except Exception:
            return 0

    @property
    def pictured_exams_count(self) -> Optional[int]:
        """Count of exams that have a capture path (OMR processed)."""
        if self.state not in [ExamState.CLOSED_AND_CAPTURE, ExamState.WARNING_HANDLING, ExamState.VALIDATION, ExamState.COMPLETED]:
            return None
        try:
            return sum(1 for e in self.exams if e.capture_path is not None) if self.exams is not None else 0
        except Exception:
            return 0

# ExamConfig schemas
class ExamConfigCreate(SQLModel):
    """Schema for creating a new exam configuration"""
    fraction: int = 0
    subject_id: int
    nmec_list: Optional[str]
    exam_name: Optional[str] = None

class ExamConfigUpdate(SQLModel):
    """Schema for updating exam configuration"""
    fraction: Optional[int] = None
    subject_id: Optional[int] = None
    nmec_list: Optional[str]

class ExamConfigRead(SQLModel):
    """Schema for reading exam configuration data"""
    id: int
    fraction: int
    subject_id: int
    status: GenerationStatus
    state: ExamState
    zip_path: Optional[str] = None
    
    # Computed metrics
    total_exams: int = 0
    associated_exams_count: Optional[int] = None
    pictured_exams_count: Optional[int] = None

class ExamConfigResponse(SQLModel):
    id: int
    subject_id: int
    fraction: int
    topic_configs: List[TopicConfigDTO] = []
    nmec_name_list: Optional[str] = None
    num_versions: int = 1
    status: GenerationStatus = GenerationStatus.PENDING
    state: ExamState = ExamState.PREPARING
    associations: List[str] = []
    
    # Computed metrics
    total_exams: int = 0
    associated_exams_count: Optional[int] = None
    pictured_exams_count: Optional[int] = None

class ExamSessionResponse(BaseModel):
    id: int
    state: ExamState
    associations: List[str]
    message: str

class StudentInfo(BaseModel):
    name: str
    nmec: str

class ExamSessionInfoResponse(BaseModel):
    id: int
    subject_id: int
    subject_name: str
    state: ExamState
    associations: List[str]
    student_list: List[StudentInfo]
    exam_ids: List[int]
    total_students: int
    total_exams: int
    role: str

class ExamSessionMetricsResponse(BaseModel):
    associated_exams_count: int
    associated_students_count: int

class ProfessorExamSessionItem(BaseModel):
    """Information about a single exam session for a professor."""
    subject_id: int
    subject_name: str
    exam_config_id: int
    state: str
    role: str
    exam_name: Optional[str]

class ExamGenerateRequest(SQLModel):
    subject_id: int
    fraction: int
    exam_name: Optional[str] = None
    topics: List[str]
    number_questions: Dict[str, int]
    relative_quotations: Dict[str, float]
    total_exams: int = 1
    number_versions: Optional[int] = None
    professors: List[str] = []
    student_tuples: List[Tuple[int, str, str]] = []
    vigilant_keycloak_ids: List[str] = []

class EvaluateBatchRequest(BaseModel):
    """Request for evaluation. List of files"""
    files: List[str]

class QRCodeToNMEC(BaseModel):
    qr: str
    nmec: int
