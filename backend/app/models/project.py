"""
Pydantic models for project operations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectCreate(BaseModel):
    """Request body for creating a new project."""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field("", max_length=2000, description="Project description")


class ProjectUpdate(BaseModel):
    """Request body for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(active|archived|completed)$")


class ProjectResponse(BaseModel):
    """Response model for a single project."""
    id: str
    name: str
    description: str = ""
    status: str = "active"
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    member_count: Optional[int] = 0
    task_count: Optional[int] = 0
    creator_name: Optional[str] = ""


class ProjectListResponse(BaseModel):
    """Response model for a list of projects."""
    projects: list[ProjectResponse]
    total: int
