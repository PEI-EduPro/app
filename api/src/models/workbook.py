# src/models/workbook.py
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship


# Workbook model
class Workbook(SQLModel, table=True):
    __tablename__ = "workbook"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    workbook_name: str = Field(max_length=100)
    workbook_xml: Optional[str] = Field(default=None)
    # Replace foreign key to local 'professor' table with Keycloak user ID
    creator_keycloak_id: str = Field(max_length=255) # Store the Keycloak ID of the creator
    
    # Relationships
    # Removed: professor: "Professor" = Relationship(back_populates="workbooks") # Professor model is gone
    # Add other relationships if needed (e.g., to subject, topic, etc.) that don't depend on Professor/Student/Manager

# Workbook schemas
class WorkbookCreate(SQLModel):
    """Schema for creating a new workbook"""
    workbook_name: str = Field(max_length=100)
    creator_keycloak_id: str  # Use Keycloak ID instead of local professor ID
    workbook_xml: Optional[str] = None

class WorkbookUpdate(SQLModel):
    """Schema for updating workbook data"""
    workbook_name: Optional[str] = Field(default=None, max_length=100)
    workbook_xml: Optional[str] = None

class WorkbookRead(SQLModel):
    """Schema for reading workbook data"""
    id: int
    workbook_name: str
    creator_keycloak_id: str  # Use Keycloak ID instead of local professor ID
    workbook_xml: Optional[str] = None

class WorkbookPublic(SQLModel):
    """Schema for public workbook data (limited info)"""
    id: int
    workbook_name: str
    # Potentially remove creator_keycloak_id from public schema if not needed
    # creator_keycloak_id: str