"""
Authentication middleware and dependency injection.
Extracts JWT from Authorization header, verifies it, and fetches user profile.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_jwt_token, get_supabase_client
from app.models.auth import UserProfile

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> UserProfile:
    """
    FastAPI dependency that extracts and verifies the JWT token,
    then returns the authenticated user's profile.
    """
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )

    supabase = get_supabase_client()
    try:
        profile_data = (
            supabase.table("profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )

        if not profile_data.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
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
            detail=f"Failed to fetch user profile: {str(e)}",
        )


async def require_verified_email(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """
    Dependency that ensures the user has verified their email.
    Use this for protected dashboard routes.
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email before accessing this resource.",
        )
    return current_user


async def require_admin(
    current_user: UserProfile = Depends(require_verified_email),
) -> UserProfile:
    """
    Dependency that ensures the user is an admin.
    Chains with email verification check.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
