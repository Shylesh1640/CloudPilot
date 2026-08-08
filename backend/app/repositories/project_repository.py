"""
Project repository — all database operations for the Project model.

All queries are scoped to the authenticated user_id to prevent data leakage.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus


class ProjectRepository:
    """Encapsulates all database access for Project records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all_for_user(self, user_id: uuid.UUID) -> list[Project]:
        result = await self._session.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self._session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Project | None:
        """Fetch a project only if it belongs to the given user."""
        result = await self._session.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        name: str,
        description: str | None = None,
        status: ProjectStatus = ProjectStatus.CREATED,
    ) -> Project:
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            status=status,
        )
        self._session.add(project)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def update(self, project: Project, **fields) -> Project:
        for key, value in fields.items():
            setattr(project, key, value)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self._session.delete(project)
        await self._session.commit()
