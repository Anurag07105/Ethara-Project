"""
Member service layer.
Handles project membership operations with Supabase.
"""

from fastapi import HTTPException, status
from app.core.security import get_supabase_client
from app.models.member import MemberAdd, MemberUpdate, MemberResponse, MemberListResponse


class MemberService:
    """Service class for project member operations."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def _enrich_member(self, m: dict) -> MemberResponse:
        r = self.supabase.table("profiles").select("email, full_name, avatar_url").eq("id", m["user_id"]).single().execute()
        p = r.data or {}
        return MemberResponse(
            id=m["id"], project_id=m["project_id"], user_id=m["user_id"],
            role=m.get("role", "member"), joined_at=m.get("joined_at"),
            user_email=p.get("email", ""), user_name=p.get("full_name", ""),
            avatar_url=p.get("avatar_url", ""),
        )

    def add_member(self, project_id: str, request: MemberAdd) -> MemberResponse:
        try:
            proj = self.supabase.table("projects").select("id").eq("id", project_id).single().execute()
            if not proj.data:
                raise HTTPException(status_code=404, detail="Project not found")
            user = self.supabase.table("profiles").select("id").eq("email", request.email).single().execute()
            if not user.data:
                raise HTTPException(status_code=404, detail="User with this email not found")
            user_id = user.data["id"]
            existing = self.supabase.table("project_members").select("id").eq("project_id", project_id).eq("user_id", user_id).execute()
            if existing.data:
                raise HTTPException(status_code=409, detail="User is already a member of this project")
            result = self.supabase.table("project_members").insert({
                "project_id": project_id, "user_id": user_id, "role": request.role or "member",
            }).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to add member")
            return self._enrich_member(result.data[0])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add member: {str(e)}")

    def get_members(self, project_id: str) -> MemberListResponse:
        try:
            result = self.supabase.table("project_members").select("*").eq("project_id", project_id).order("joined_at", desc=False).execute()
            members = [self._enrich_member(m) for m in (result.data or [])]
            return MemberListResponse(members=members, total=len(members))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch members: {str(e)}")

    def update_member_role(self, project_id: str, member_id: str, request: MemberUpdate) -> MemberResponse:
        try:
            existing = self.supabase.table("project_members").select("*").eq("id", member_id).eq("project_id", project_id).single().execute()
            if not existing.data:
                raise HTTPException(status_code=404, detail="Member not found")
            if existing.data.get("role") == "owner":
                raise HTTPException(status_code=400, detail="Cannot change the role of the project owner")
            result = self.supabase.table("project_members").update({"role": request.role}).eq("id", member_id).execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Member not found")
            return self._enrich_member(result.data[0])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update member: {str(e)}")

    def remove_member(self, project_id: str, member_id: str) -> dict:
        try:
            existing = self.supabase.table("project_members").select("*").eq("id", member_id).eq("project_id", project_id).single().execute()
            if not existing.data:
                raise HTTPException(status_code=404, detail="Member not found")
            if existing.data.get("role") == "owner":
                raise HTTPException(status_code=400, detail="Cannot remove the project owner")
            self.supabase.table("project_members").delete().eq("id", member_id).execute()
            return {"message": "Member removed successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to remove member: {str(e)}")
