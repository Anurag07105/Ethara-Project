"""
Pydantic models for project member operations.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class MemberAdd(BaseModel):
    """Request body for adding a member to a project."""
    email: EmailStr = Field(..., description="Email of the user to add")
    role: Optional[str] = Field("member", pattern="^(admin|member)$", description="Role within the project")


class MemberUpdate(BaseModel):
    """Request body for updating a member's role."""
    role: str = Field(..., pattern="^(admin|member)$", description="New role for the member")


class MemberResponse(BaseModel):
    """Response model for a project member."""
    id: str
    project_id: str
    user_id: str
    role: str = "member"
    joined_at: Optional[datetime] = None
    user_email: Optional[str] = ""
    user_name: Optional[str] = ""
    avatar_url: Optional[str] = ""


class MemberListResponse(BaseModel):
    """Response model for a list of project members."""
    members: list[MemberResponse]
    total: int
