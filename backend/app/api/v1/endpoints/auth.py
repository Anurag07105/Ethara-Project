"""
Authentication API endpoints.
Handles signup, login, token refresh, profile management, and admin user operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.auth import (
    SignUpRequest, SignInRequest, AuthResponse, UserProfile,
    UpdateProfileRequest, ForgotPasswordRequest, TokenRefreshRequest,
)
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user, require_verified_email, require_admin

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest):
    """Register a new user account."""
    service = AuthService()
    return service.sign_up(request)


@router.post("/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """Authenticate and receive access tokens."""
    service = AuthService()
    return service.sign_in(request)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: TokenRefreshRequest):
    """Refresh an expired access token."""
    service = AuthService()
    return service.refresh_token(request.refresh_token)


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send a password reset email."""
    service = AuthService()
    return service.forgot_password(request.email)


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: UserProfile = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.put("/me", response_model=UserProfile)
async def update_me(
    request: UpdateProfileRequest,
    current_user: UserProfile = Depends(require_verified_email),
):
    """Update the current user's profile."""
    service = AuthService()
    return service.update_profile(current_user.id, request)


@router.get("/users", response_model=list[UserProfile])
async def get_all_users(current_user: UserProfile = Depends(require_admin)):
    """Get all users. Admin only."""
    service = AuthService()
    return service.get_all_users()


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: UserProfile = Depends(require_admin),
):
    """Update a user's global role. Admin only."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot change your own role")
    service = AuthService()
    return service.update_user_role(user_id, role)
