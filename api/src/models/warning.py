from typing import Optional, List
from sqlmodel import Field, SQLModel, Column, JSON
from enum import Enum

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
