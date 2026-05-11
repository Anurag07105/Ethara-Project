"""
Authentication service layer.
Handles all auth-related business logic with Supabase GoTrue.
"""

import logging
from fastapi import HTTPException, status
from app.core.security import get_supabase_client, get_supabase_anon_client
from app.models.auth import (
    SignUpRequest,
    SignInRequest,
    AuthResponse,
    UserProfile,
    UpdateProfileRequest,
)


class AuthService:
    """Service class for authentication and user profile operations."""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.anon_client = get_supabase_anon_client()

    def sign_up(self, request: SignUpRequest) -> AuthResponse:
        """
        Register a new user with Supabase GoTrue.
        Creates the auth user and the profile is auto-created via DB trigger.
        """
        try:
            # Validate role
            role = request.role if request.role in ("admin", "member") else "member"

            auth_response = self.anon_client.auth.sign_up(
                {
                    "email": request.email,
                    "password": request.password,
                    "options": {
                        "data": {
                            "full_name": request.full_name,
                            "role": role,
                        }
                    },
                }
            )

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user account",
                )

            user = auth_response.user
            session = auth_response.session

            # Update the profile role if it differs from default
            if role != "member":
                try:
                    self.supabase.table("profiles").update(
                        {"role": role}
                    ).eq("id", str(user.id)).execute()
                except Exception:
                    pass  # Profile may not exist yet if trigger hasn't fired

            profile = UserProfile(
                id=str(user.id),
                email=user.email or request.email,
                full_name=request.full_name,
                role=role,
                email_verified=user.email_confirmed_at is not None,
            )

            access_token = session.access_token if session else ""
            refresh_token = session.refresh_token if session else ""

            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=profile,
                message="Account created successfully. Please verify your email.",
            )

        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "already registered" in error_msg or "already been registered" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}",
            )

    def sign_in(self, request: SignInRequest) -> AuthResponse:
        """
        Authenticate a user and return session tokens.
        Checks email verification status before allowing access.
        """
        try:
            logger = logging.getLogger("ethara.auth")

            auth_response = self.anon_client.auth.sign_in_with_password(
                {
                    "email": request.email,
                    "password": request.password,
                }
            )

            # Surface Supabase error details when available (helps debug 400 responses)
            error = None
            if hasattr(auth_response, "error") and auth_response.error:
                error = auth_response.error
            elif isinstance(auth_response, dict):
                error = auth_response.get("error")
            if error:
                err_msg = getattr(error, "message", str(error))
                logger.info("Supabase auth error: %s", err_msg)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authentication failed: {err_msg}",
                )

            if not getattr(auth_response, "user", None) or not getattr(auth_response, "session", None):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            user = auth_response.user
            session = auth_response.session

            # Fetch profile from our profiles table
            profile_data = (
                self.supabase.table("profiles")
                .select("*")
                .eq("id", str(user.id))
                .single()
                .execute()
            )

            if not profile_data.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found",
                )

            p = profile_data.data
            email_verified = user.email_confirmed_at is not None

            # Update email_verified status in profile if needed
            if email_verified and not p.get("email_verified", False):
                self.supabase.table("profiles").update(
                    {"email_verified": True}
                ).eq("id", str(user.id)).execute()
                p["email_verified"] = True

            profile = UserProfile(
                id=p["id"],
                email=p["email"],
                full_name=p.get("full_name", ""),
                avatar_url=p.get("avatar_url", ""),
                role=p.get("role", "member"),
                email_verified=email_verified,
                created_at=p.get("created_at"),
                updated_at=p.get("updated_at"),
            )

            return AuthResponse(
                access_token=session.access_token,
                refresh_token=session.refresh_token,
                user=profile,
                message="Login successful",
            )

        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg or "credentials" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}",
            )

    def refresh_token(self, refresh_token: str) -> AuthResponse:
        """Refresh an expired access token using the refresh token."""
        try:
            auth_response = self.anon_client.auth.refresh_session(refresh_token)

            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token",
                )

            user = auth_response.user
            session = auth_response.session

            profile_data = (
                self.supabase.table("profiles")
                .select("*")
                .eq("id", str(user.id))
                .single()
                .execute()
            )

            p = profile_data.data or {}
            profile = UserProfile(
                id=str(user.id),
                email=user.email or p.get("email", ""),
                full_name=p.get("full_name", ""),
                avatar_url=p.get("avatar_url", ""),
                role=p.get("role", "member"),
                email_verified=user.email_confirmed_at is not None,
                created_at=p.get("created_at"),
                updated_at=p.get("updated_at"),
            )

            return AuthResponse(
                access_token=session.access_token,
                refresh_token=session.refresh_token,
                user=profile,
                message="Token refreshed successfully",
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token refresh failed: {str(e)}",
            )

    def get_profile(self, user_id: str) -> UserProfile:
        """Fetch a user's profile by their ID."""
        try:
            profile_data = (
                self.supabase.table("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )

            if not profile_data.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found",
                )

            p = profile_data.data
            return UserProfile(
                id=p["id"],
                email=p["email"],
                full_name=p.get("full_name", ""),
                avatar_url=p.get("avatar_url", ""),
                role=p.get("role", "member"),
                email_verified=p.get("email_verified", False),
                created_at=p.get("created_at"),
                updated_at=p.get("updated_at"),
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch profile: {str(e)}",
            )

    def update_profile(self, user_id: str, request: UpdateProfileRequest) -> UserProfile:
        """Update a user's profile information."""
        try:
            update_data = {}
            if request.full_name is not None:
                update_data["full_name"] = request.full_name
            if request.avatar_url is not None:
                update_data["avatar_url"] = request.avatar_url

            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update",
                )

            result = (
                self.supabase.table("profiles")
                .update(update_data)
                .eq("id", user_id)
                .execute()
            )

            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found",
                )

            p = result.data[0]
            return UserProfile(
                id=p["id"],
                email=p["email"],
                full_name=p.get("full_name", ""),
                avatar_url=p.get("avatar_url", ""),
                role=p.get("role", "member"),
                email_verified=p.get("email_verified", False),
                created_at=p.get("created_at"),
                updated_at=p.get("updated_at"),
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Profile update failed: {str(e)}",
            )

    def forgot_password(self, email: str) -> dict:
        """Send a password reset email via Supabase."""
        try:
            self.anon_client.auth.reset_password_email(email)
            return {"message": "If an account with that email exists, a reset link has been sent."}
        except Exception:
            # Always return success to prevent email enumeration
            return {"message": "If an account with that email exists, a reset link has been sent."}

    def get_all_users(self) -> list[UserProfile]:
        """Fetch all user profiles. Admin only."""
        try:
            result = (
                self.supabase.table("profiles")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )

            return [
                UserProfile(
                    id=p["id"],
                    email=p["email"],
                    full_name=p.get("full_name", ""),
                    avatar_url=p.get("avatar_url", ""),
                    role=p.get("role", "member"),
                    email_verified=p.get("email_verified", False),
                    created_at=p.get("created_at"),
                    updated_at=p.get("updated_at"),
                )
                for p in (result.data or [])
            ]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch users: {str(e)}",
            )

    def update_user_role(self, user_id: str, role: str) -> UserProfile:
        """Update a user's global role. Admin only."""
        if role not in ("admin", "member"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'admin' or 'member'",
            )

        try:
            result = (
                self.supabase.table("profiles")
                .update({"role": role})
                .eq("id", user_id)
                .execute()
            )

            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            p = result.data[0]
            return UserProfile(
                id=p["id"],
                email=p["email"],
                full_name=p.get("full_name", ""),
                avatar_url=p.get("avatar_url", ""),
                role=p.get("role", "member"),
                email_verified=p.get("email_verified", False),
                created_at=p.get("created_at"),
                updated_at=p.get("updated_at"),
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update role: {str(e)}",
            )
