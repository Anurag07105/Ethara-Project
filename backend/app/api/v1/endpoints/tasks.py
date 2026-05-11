"""
Tasks API endpoints.
CRUD operations for tasks with RBAC enforcement.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.models.auth import UserProfile
from app.models.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from app.services.task_service import TaskService
from app.middleware.auth_middleware import require_verified_email, require_admin

router = APIRouter()


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    current_user: UserProfile = Depends(require_verified_email),
):
    """
    List tasks. Admins see all tasks, members see tasks from their projects.
    Optionally filter by project_id.
    """
    service = TaskService()
    if project_id:
        return service.get_tasks_by_project(project_id, current_user.id, current_user.role)
    if current_user.role == "admin":
        return service.get_all_tasks()
    return service.get_my_tasks(current_user.id)


@router.get("/my-tasks", response_model=TaskListResponse)
async def get_my_tasks(current_user: UserProfile = Depends(require_verified_email)):
    """Get all tasks assigned to the current user."""
    service = TaskService()
    return service.get_my_tasks(current_user.id)


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    request: TaskCreate,
    current_user: UserProfile = Depends(require_admin),
):
    """Create a new task. Admin only."""
    service = TaskService()
    return service.create_task(request, current_user.id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: UserProfile = Depends(require_verified_email),
):
    """Get a single task by ID."""
    service = TaskService()
    return service.get_task(task_id, current_user.id, current_user.role)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: TaskUpdate,
    current_user: UserProfile = Depends(require_verified_email),
):
    """Update a task. Admins can update any task, members can update assigned tasks only."""
    service = TaskService()
    return service.update_task(task_id, request, current_user.id, current_user.role)


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: UserProfile = Depends(require_admin),
):
    """Delete a task. Admin only."""
    service = TaskService()
    return service.delete_task(task_id)
