"""
Pydantic models for task operations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCreate(BaseModel):
    """Request body for creating a new task."""
    project_id: str = Field(..., description="UUID of the project this task belongs to")
    title: str = Field(..., min_length=1, max_length=300, description="Task title")
    description: Optional[str] = Field("", max_length=5000, description="Task description")
    status: Optional[str] = Field("todo", pattern="^(todo|in_progress|review|done)$")
    priority: Optional[str] = Field("medium", pattern="^(low|medium|high|urgent)$")
    assigned_to: Optional[str] = Field(None, description="UUID of the assigned user")
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Request body for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[str] = Field(None, pattern="^(todo|in_progress|review|done)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Response model for a single task."""
    id: str
    project_id: str
    title: str
    description: str = ""
    status: str = "todo"
    priority: str = "medium"
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = ""
    created_by: str
    creator_name: Optional[str] = ""
    due_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    project_name: Optional[str] = ""


class TaskListResponse(BaseModel):
    """Response model for a list of tasks."""
    tasks: list[TaskResponse]
    total: int
