"""
Pydantic models for authentication and user profile operations.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SignUpRequest(BaseModel):
    """Request body for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    role: Optional[str] = Field("member", description="User role: 'admin' or 'member'")


class SignInRequest(BaseModel):
    """Request body for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    """Request body for forgot password."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request body for password reset."""
    new_password: str = Field(..., min_length=8, max_length=128)


class UserProfile(BaseModel):
    """Response model for user profile data."""
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = ""
    role: str = "member"
    email_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    """Request body for updating user profile."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None


class AuthResponse(BaseModel):
    """Response model for authentication operations."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfile
    message: str = "Success"


class TokenRefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str
