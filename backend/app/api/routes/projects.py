"""Project CRUD routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "",
    response_model=list[ProjectRead],
    summary="List all projects",
    description="Return all projects belonging to the authenticated user, ordered by creation date (newest first).",
    responses={
        200: {"description": "List of projects"},
        401: {"description": "Not authenticated"},
    },
)
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ProjectRead]:
    service = ProjectService(session)
    return await service.list_projects(current_user.id)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    description="Create a new CloudPilot project. GitHub repository connection is implemented in Phase 2.",
    responses={
        201: {"description": "Project created"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    },
)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(session)
    return await service.create_project(data, current_user.id)


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get a project",
    description="Return a single project by ID. Returns 404 if the project does not exist or belongs to a different user.",
    responses={
        200: {"description": "Project details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Project not found"},
    },
)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(session)
    return await service.get_project(project_id, current_user.id)


@router.put(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Update a project",
    description="Update project fields. All fields are optional (partial update).",
    responses={
        200: {"description": "Updated project"},
        401: {"description": "Not authenticated"},
        404: {"description": "Project not found"},
    },
)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(session)
    return await service.update_project(project_id, data, current_user.id)


@router.delete(
    "/{project_id}",
    summary="Delete a project",
    description="Permanently delete a project and all associated data. This action cannot be undone.",
    responses={
        204: {"description": "Project deleted"},
        401: {"description": "Not authenticated"},
        404: {"description": "Project not found"},
    },
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    service = ProjectService(session)
    await service.delete_project(project_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
