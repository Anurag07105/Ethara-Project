"""
Members API endpoints.
Manages project membership with admin-only access.
"""

from fastapi import APIRouter, Depends

from app.models.auth import UserProfile
from app.models.member import MemberAdd, MemberUpdate, MemberResponse, MemberListResponse
from app.services.member_service import MemberService
from app.middleware.auth_middleware import require_verified_email, require_admin

router = APIRouter()


@router.get("/{project_id}", response_model=MemberListResponse)
async def list_members(
    project_id: str,
    current_user: UserProfile = Depends(require_verified_email),
):
    """List all members of a project."""
    service = MemberService()
    return service.get_members(project_id)


@router.post("/{project_id}", response_model=MemberResponse, status_code=201)
async def add_member(
    project_id: str,
    request: MemberAdd,
    current_user: UserProfile = Depends(require_admin),
):
    """Add a member to a project. Admin only."""
    service = MemberService()
    return service.add_member(project_id, request)


@router.put("/{project_id}/{member_id}", response_model=MemberResponse)
async def update_member_role(
    project_id: str,
    member_id: str,
    request: MemberUpdate,
    current_user: UserProfile = Depends(require_admin),
):
    """Update a member's role in a project. Admin only."""
    service = MemberService()
    return service.update_member_role(project_id, member_id, request)


@router.delete("/{project_id}/{member_id}")
async def remove_member(
    project_id: str,
    member_id: str,
    current_user: UserProfile = Depends(require_admin),
):
    """Remove a member from a project. Admin only."""
    service = MemberService()
    return service.remove_member(project_id, member_id)
