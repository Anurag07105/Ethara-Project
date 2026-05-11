"""
Project service layer.
Handles all project-related business logic with Supabase.
"""

from fastapi import HTTPException, status
from app.core.security import get_supabase_client
from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse


class ProjectService:
    """Service class for project CRUD operations."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def _get_counts(self, project_id: str) -> tuple[int, int]:
        mc = self.supabase.table("project_members").select("id", count="exact").eq("project_id", project_id).execute()
        tc = self.supabase.table("tasks").select("id", count="exact").eq("project_id", project_id).execute()
        return (mc.count or 0, tc.count or 0)

    def _get_creator_name(self, user_id: str) -> str:
        r = self.supabase.table("profiles").select("full_name").eq("id", user_id).single().execute()
        return r.data.get("full_name", "") if r.data else ""

    def _to_response(self, p: dict) -> ProjectResponse:
        mc, tc = self._get_counts(p["id"])
        return ProjectResponse(
            id=p["id"], name=p["name"], description=p.get("description", ""),
            status=p.get("status", "active"), created_by=p["created_by"],
            created_at=p.get("created_at"), updated_at=p.get("updated_at"),
            member_count=mc, task_count=tc, creator_name=self._get_creator_name(p["created_by"]),
        )

    def create_project(self, request: ProjectCreate, user_id: str) -> ProjectResponse:
        try:
            result = self.supabase.table("projects").insert({
                "name": request.name, "description": request.description or "",
                "status": "active", "created_by": user_id,
            }).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create project")
            project = result.data[0]
            self.supabase.table("project_members").insert({
                "project_id": project["id"], "user_id": user_id, "role": "owner",
            }).execute()
            return self._to_response(project)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

    def get_projects(self, user_id: str, user_role: str) -> ProjectListResponse:
        try:
            if user_role == "admin":
                result = self.supabase.table("projects").select("*").order("created_at", desc=True).execute()
            else:
                memberships = self.supabase.table("project_members").select("project_id").eq("user_id", user_id).execute()
                project_ids = [m["project_id"] for m in (memberships.data or [])]
                if not project_ids:
                    return ProjectListResponse(projects=[], total=0)
                result = self.supabase.table("projects").select("*").in_("id", project_ids).order("created_at", desc=True).execute()
            projects = [self._to_response(p) for p in (result.data or [])]
            return ProjectListResponse(projects=projects, total=len(projects))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

    def get_project(self, project_id: str, user_id: str, user_role: str) -> ProjectResponse:
        try:
            result = self.supabase.table("projects").select("*").eq("id", project_id).single().execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Project not found")
            if user_role != "admin":
                m = self.supabase.table("project_members").select("id").eq("project_id", project_id).eq("user_id", user_id).execute()
                if not m.data:
                    raise HTTPException(status_code=403, detail="You do not have access to this project")
            return self._to_response(result.data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch project: {str(e)}")

    def update_project(self, project_id: str, request: ProjectUpdate) -> ProjectResponse:
        try:
            update_data = {}
            if request.name is not None:
                update_data["name"] = request.name
            if request.description is not None:
                update_data["description"] = request.description
            if request.status is not None:
                update_data["status"] = request.status
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            result = self.supabase.table("projects").update(update_data).eq("id", project_id).execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Project not found")
            return self._to_response(result.data[0])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

    def delete_project(self, project_id: str) -> dict:
        try:
            existing = self.supabase.table("projects").select("id").eq("id", project_id).single().execute()
            if not existing.data:
                raise HTTPException(status_code=404, detail="Project not found")
            self.supabase.table("projects").delete().eq("id", project_id).execute()
            return {"message": "Project deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

    def get_project_stats(self, user_id: str, user_role: str) -> dict:
        try:
            if user_role == "admin":
                tp = self.supabase.table("projects").select("id", count="exact").execute()
                ap = self.supabase.table("projects").select("id", count="exact").eq("status", "active").execute()
                tt = self.supabase.table("tasks").select("id", count="exact").execute()
                ct = self.supabase.table("tasks").select("id", count="exact").eq("status", "done").execute()
                tm = self.supabase.table("profiles").select("id", count="exact").execute()
                return {"total_projects": tp.count or 0, "active_projects": ap.count or 0,
                        "total_tasks": tt.count or 0, "completed_tasks": ct.count or 0, "total_members": tm.count or 0}
            else:
                memberships = self.supabase.table("project_members").select("project_id").eq("user_id", user_id).execute()
                pids = [m["project_id"] for m in (memberships.data or [])]
                if not pids:
                    return {"total_projects": 0, "active_projects": 0, "total_tasks": 0, "completed_tasks": 0, "total_members": 0}
                ap = self.supabase.table("projects").select("id", count="exact").in_("id", pids).eq("status", "active").execute()
                tt = self.supabase.table("tasks").select("id", count="exact").in_("project_id", pids).execute()
                ct = self.supabase.table("tasks").select("id", count="exact").in_("project_id", pids).eq("status", "done").execute()
                return {"total_projects": len(pids), "active_projects": ap.count or 0,
                        "total_tasks": tt.count or 0, "completed_tasks": ct.count or 0, "total_members": 0}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")
