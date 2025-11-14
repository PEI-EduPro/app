from typing import Optional
from sqlmodel import Field, SQLModel, Relationship


# Workbook model
class Workbook(SQLModel, table=True):
    __tablename__ = "workbook"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    workbook_name: str = Field(max_length=100)
    workbook_xml: Optional[str] = Field(default=None)
    professor_id: int = Field(foreign_key="professor.id")
    
    # Relationships
    professor: "Professor" = Relationship(back_populates="workbooks")

# Workbook schemas
class WorkbookCreate(SQLModel):
    """Schema for creating a new workbook"""
    workbook_name: str = Field(max_length=100)
    professor_id: int
    workbook_xml: Optional[str] = None

class WorkbookUpdate(SQLModel):
    """Schema for updating workbook data"""
    workbook_name: Optional[str] = Field(default=None, max_length=100)
    workbook_xml: Optional[str] = None

class WorkbookRead(SQLModel):
    """Schema for reading workbook data"""
    id: int
    workbook_name: str
    professor_id: int
    workbook_xml: Optional[str] = None

class WorkbookPublic(SQLModel):
    """Schema for public workbook data (limited info)"""
    id: int
    workbook_name: str
    professor_id: int