from typing import Optional, List
from .subject import ProfessorSubjectLink, StudentSubjectLink
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


class UserRole(str, Enum):
    MANAGER = "manager"
    PROFESSOR = "professor"
    STUDENT = "student"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    keycloak_id: str = Field(unique=True, index=True)
    mechanographic_number: Optional[str] = Field(default=None, unique=True, index=True)
    email: str = Field(unique=True, index=True)
    name: str
    role: UserRole = Field(default=UserRole.STUDENT)
    is_active: bool = Field(default=True)

class UserCreate(SQLModel):
    keycloak_id: str
    email: str
    name: str
    mechanographic_number: Optional[str] = None
    role: UserRole = UserRole.STUDENT

class UserRead(SQLModel):
    id: int
    email: str
    name: str
    mechanographic_number: Optional[str]
    role: UserRole
    is_active: bool

class UserUpdate(SQLModel):
    """Schema for updating user data"""
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)
    

class Student(SQLModel, table=True):
    __tablename__ = "student"
    
    id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    
    subjects: List["Subject"] = Relationship(
        back_populates="students",
        link_model=StudentSubjectLink
    )

# Student schemas
class StudentCreate(SQLModel):
    """Schema for creating a new student"""
    name: str = Field(max_length=100)
    email: str = Field(max_length=100)

class StudentUpdate(SQLModel):
    """Schema for updating student data"""
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)

class StudentRead(SQLModel):
    """Schema for reading student data"""
    id: int
    name: str
    email: str
    user_type: str

class StudentPublic(SQLModel):
    """Schema for public student data (limited info)"""
    id: int
    name: str
    email: str


class Professor(SQLModel, table=True):
    __tablename__ = "professor"
    
    id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    
    subjects: List["Subject"] = Relationship(
        back_populates="professors",
        link_model=ProfessorSubjectLink
    )
    workbooks: List["Workbook"] = Relationship(back_populates="professor")
    exam_configs: List["ExamConfig"] = Relationship(back_populates="professor")

# Professor schemas
class ProfessorCreate(SQLModel):
    """Schema for creating a new professor"""
    name: str = Field(max_length=100)
    email: str = Field(max_length=100)

class ProfessorUpdate(SQLModel):
    """Schema for updating professor data"""
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)

class ProfessorRead(SQLModel):
    """Schema for reading professor data"""
    id: int
    name: str
    email: str
    user_type: str

class ProfessorPublic(SQLModel):
    """Schema for public professor data (limited info)"""
    id: int
    name: str


class Manager(SQLModel, table=True):
    __tablename__ = "manager"
    
    id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    
    subjects_created: List["Subject"] = Relationship(back_populates="manager")

# Manager schemas
class ManagerCreate(SQLModel):
    """Schema for creating a new manager"""
    name: str = Field(max_length=100)
    email: str = Field(max_length=100)

class ManagerUpdate(SQLModel):
    """Schema for updating manager data"""
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)

class ManagerRead(SQLModel):
    """Schema for reading manager data"""
    id: int
    name: str
    email: str
    user_type: str

class ManagerPublic(SQLModel):
    """Schema for public manager data (limited info)"""
    id: int
    name: str