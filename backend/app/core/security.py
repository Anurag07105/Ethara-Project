"""
Security utilities for JWT verification and Supabase client initialization.
"""

from supabase import create_client, Client
from jose import jwt, JWTError
from fastapi import HTTPException, status

from app.core.config import get_settings


def get_supabase_client() -> Client:
    """
    Returns a Supabase client using the service role key.
    The service role key bypasses RLS for backend operations.
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon_client() -> Client:
    """
    Returns a Supabase client using the anon/public key.
    Used for auth operations that should respect RLS.
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode a Supabase JWT token.

    Args:
        token: The JWT token string from the Authorization header.

    Returns:
        The decoded token payload containing user info.

    Raises:
        HTTPException: If the token is invalid, expired, or malformed.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject claim",
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )
