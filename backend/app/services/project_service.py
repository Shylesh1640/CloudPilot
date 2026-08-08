"""
Project service — business logic for project CRUD operations.

Route → ProjectService → ProjectRepository → SQLAlchemy
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate


class ProjectService:
    """
    Handles project lifecycle management.

    All operations verify that the requesting user owns the project.
    GitHub integration and deployment orchestration are implemented in Phase 2+.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProjectRepository(session)

    async def list_projects(self, user_id: uuid.UUID) -> list[ProjectRead]:
        """Return all projects belonging to the authenticated user."""
        projects = await self._repo.get_all_for_user(user_id)
        return [ProjectRead.model_validate(p) for p in projects]

    async def get_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectRead:
        """
        Return a single project by ID.

        Raises:
            HTTPException 404: If project does not exist or doesn't belong to user.
        """
        project = await self._repo.get_by_id_for_user(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": "Project was not found.",
                    },
                },
            )
        return ProjectRead.model_validate(project)

    async def create_project(
        self, data: ProjectCreate, user_id: uuid.UUID
    ) -> ProjectRead:
        """Create a new project for the authenticated user."""
        project = await self._repo.create(
            user_id=user_id,
            name=data.name,
            description=data.description,
        )
        return ProjectRead.model_validate(project)

    async def update_project(
        self,
        project_id: uuid.UUID,
        data: ProjectUpdate,
        user_id: uuid.UUID,
    ) -> ProjectRead:
        """
        Update a project's fields.

        Raises:
            HTTPException 404: If project does not exist or doesn't belong to user.
        """
        project = await self._repo.get_by_id_for_user(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": "Project was not found.",
                    },
                },
            )
        update_data = data.model_dump(exclude_unset=True)
        updated = await self._repo.update(project, **update_data)
        return ProjectRead.model_validate(updated)

    async def delete_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """
        Delete a project.

        Raises:
            HTTPException 404: If project does not exist or doesn't belong to user.
        """
        project = await self._repo.get_by_id_for_user(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": "Project was not found.",
                    },
                },
            )
        await self._repo.delete(project)
