"""
Task service layer.
Handles all task-related business logic with Supabase.
"""

from fastapi import HTTPException, status
from app.core.security import get_supabase_client
from app.models.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse


class TaskService:
    """Service class for task CRUD operations."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def _enrich_task(self, t: dict) -> TaskResponse:
        assigned_name = ""
        if t.get("assigned_to"):
            r = self.supabase.table("profiles").select("full_name").eq("id", t["assigned_to"]).single().execute()
            assigned_name = r.data.get("full_name", "") if r.data else ""
        cr = self.supabase.table("profiles").select("full_name").eq("id", t["created_by"]).single().execute()
        creator_name = cr.data.get("full_name", "") if cr.data else ""
        pr = self.supabase.table("projects").select("name").eq("id", t["project_id"]).single().execute()
        project_name = pr.data.get("name", "") if pr.data else ""
        return TaskResponse(
            id=t["id"], project_id=t["project_id"], title=t["title"],
            description=t.get("description", ""), status=t.get("status", "todo"),
            priority=t.get("priority", "medium"), assigned_to=t.get("assigned_to"),
            assigned_to_name=assigned_name, created_by=t["created_by"],
            creator_name=creator_name, due_date=t.get("due_date"),
            created_at=t.get("created_at"), updated_at=t.get("updated_at"),
            project_name=project_name,
        )

    def create_task(self, request: TaskCreate, user_id: str) -> TaskResponse:
        try:
            proj = self.supabase.table("projects").select("id").eq("id", request.project_id).single().execute()
            if not proj.data:
                raise HTTPException(status_code=404, detail="Project not found")
            if request.assigned_to:
                mem = self.supabase.table("project_members").select("id").eq("project_id", request.project_id).eq("user_id", request.assigned_to).execute()
                if not mem.data:
                    raise HTTPException(status_code=400, detail="Assigned user is not a member of this project")
            task_data = {
                "project_id": request.project_id, "title": request.title,
                "description": request.description or "", "status": request.status or "todo",
                "priority": request.priority or "medium", "created_by": user_id,
            }
            if request.assigned_to:
                task_data["assigned_to"] = request.assigned_to
            if request.due_date:
                task_data["due_date"] = request.due_date.isoformat()
            result = self.supabase.table("tasks").insert(task_data).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create task")
            return self._enrich_task(result.data[0])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

    def get_tasks_by_project(self, project_id: str, user_id: str, user_role: str) -> TaskListResponse:
        try:
            if user_role != "admin":
                m = self.supabase.table("project_members").select("id").eq("project_id", project_id).eq("user_id", user_id).execute()
                if not m.data:
                    raise HTTPException(status_code=403, detail="You do not have access to this project")
            result = self.supabase.table("tasks").select("*").eq("project_id", project_id).order("created_at", desc=True).execute()
            tasks = [self._enrich_task(t) for t in (result.data or [])]
            return TaskListResponse(tasks=tasks, total=len(tasks))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

    def get_my_tasks(self, user_id: str) -> TaskListResponse:
        try:
            result = self.supabase.table("tasks").select("*").eq("assigned_to", user_id).order("created_at", desc=True).execute()
            tasks = [self._enrich_task(t) for t in (result.data or [])]
            return TaskListResponse(tasks=tasks, total=len(tasks))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

    def get_all_tasks(self) -> TaskListResponse:
        try:
            result = self.supabase.table("tasks").select("*").order("created_at", desc=True).execute()
            tasks = [self._enrich_task(t) for t in (result.data or [])]
            return TaskListResponse(tasks=tasks, total=len(tasks))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

    def get_task(self, task_id: str, user_id: str, user_role: str) -> TaskResponse:
        try:
            result = self.supabase.table("tasks").select("*").eq("id", task_id).single().execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Task not found")
            t = result.data
            if user_role != "admin":
                m = self.supabase.table("project_members").select("id").eq("project_id", t["project_id"]).eq("user_id", user_id).execute()
                if not m.data:
                    raise HTTPException(status_code=403, detail="You do not have access to this task")
            return self._enrich_task(t)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")

    def update_task(self, task_id: str, request: TaskUpdate, user_id: str, user_role: str) -> TaskResponse:
        try:
            existing = self.supabase.table("tasks").select("*").eq("id", task_id).single().execute()
            if not existing.data:
                raise HTTPException(status_code=404, detail="Task not found")
            t = existing.data
            if user_role != "admin":
                if t.get("assigned_to") != user_id:
                    raise HTTPException(status_code=403, detail="You can only update tasks assigned to you")
            update_data = {}
            if request.title is not None:
                update_data["title"] = request.title
            if request.description is not None:
                update_data["description"] = request.description
            if request.status is not None:
                update_data["status"] = request.status
            if request.priority is not None:
                update_data["priority"] = request.priority
            if request.assigned_to is not None:
                mem = self.supabase.table("project_members").select("id").eq("project_id", t["project_id"]).eq("user_id", request.assigned_to).execute()
                if not mem.data:
                    raise HTTPException(status_code=400, detail="Assigned user is not a member of this project")
                update_data["assigned_to"] = request.assigned_to
            if request.due_date is not None:
                update_data["due_date"] = request.due_date.isoformat()
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            result = self.supabase.table("tasks").update(update_data).eq("id", task_id).execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Task not found")
            return self._enrich_task(result.data[0])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

    def delete_task(self, task_id: str) -> dict:
        try:
            existing = self.supabase.table("tasks").select("id").eq("id", task_id).single().execute()
            if not existing.data:
                raise HTTPException(status_code=404, detail="Task not found")
            self.supabase.table("tasks").delete().eq("id", task_id).execute()
            return {"message": "Task deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")
