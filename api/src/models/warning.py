from typing import Optional, List
from sqlmodel import Field, SQLModel, Column, JSON
from enum import Enum
from pydantic import BaseModel


class WarningType(str, Enum):
    multiple_students_to_exam = "multiple_students_to_exam"
    multiple_exams_to_student = "multiple_exams_to_student"
    exam_correction_no_student = "exam_correction_no_student"


class Warning(SQLModel, table=True):
    __tablename__ = "warning"

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_config_id: int = Field(foreign_key="exam_config.id")
    type: WarningType
    student_list: Optional[str] = Field(default=None, description="String with a tuple nmec:name")
    exam_list: List[int] = Field(default=[], sa_column=Column(JSON), description="IDs of the multiple exams")


class StudentWarningInfo(BaseModel):
    nmec: int
    name: str
    email: str


class ExamWarningResponse(BaseModel):
    exam_id: int
    batch_number: Optional[int] = None
    students: List[StudentWarningInfo]


class StudentSummary(BaseModel):
    nmec: str
    name: str
    email: str


class WarningsWithStudentsResponse(BaseModel):
    warnings: List[ExamWarningResponse]
    students: List[StudentSummary]


class WarningAssignment(BaseModel):
    exam_id: int
    student_nmec: str


class ResolveWarningsRequest(BaseModel):
    assignments: List[WarningAssignment]
