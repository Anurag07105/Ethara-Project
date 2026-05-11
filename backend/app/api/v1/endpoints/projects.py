"""
Projects API endpoints.
CRUD operations for projects with RBAC enforcement.
"""

from fastapi import APIRouter, Depends

from app.models.auth import UserProfile
from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.services.project_service import ProjectService
from app.middleware.auth_middleware import require_verified_email, require_admin

router = APIRouter()


@router.get("/", response_model=ProjectListResponse)
async def list_projects(current_user: UserProfile = Depends(require_verified_email)):
    """List projects accessible to the current user."""
    service = ProjectService()
    return service.get_projects(current_user.id, current_user.role)


@router.get("/stats")
async def get_stats(current_user: UserProfile = Depends(require_verified_email)):
    """Get dashboard statistics."""
    service = ProjectService()
    return service.get_project_stats(current_user.id, current_user.role)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: ProjectCreate,
    current_user: UserProfile = Depends(require_admin),
):
    """Create a new project. Admin only."""
    service = ProjectService()
    return service.create_project(request, current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: UserProfile = Depends(require_verified_email),
):
    """Get a single project by ID."""
    service = ProjectService()
    return service.get_project(project_id, current_user.id, current_user.role)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    current_user: UserProfile = Depends(require_admin),
):
    """Update a project. Admin only."""
    service = ProjectService()
    return service.update_project(project_id, request)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: UserProfile = Depends(require_admin),
):
    """Delete a project. Admin only."""
    service = ProjectService()
    return service.delete_project(project_id)
