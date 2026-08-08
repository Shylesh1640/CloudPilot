"""Database access layer for repository analyses."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository_analysis import AnalysisStatus, RepositoryAnalysis


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        project_id: uuid.UUID,
        repository_url: str,
        repository_owner: str,
        repository_name: str,
    ) -> RepositoryAnalysis:
        analysis = RepositoryAnalysis(
            project_id=project_id,
            repository_url=repository_url,
            repository_owner=repository_owner,
            repository_name=repository_name,
            status=AnalysisStatus.PENDING,
            progress=0,
        )
        self._session.add(analysis)
        await self._session.commit()
        await self._session.refresh(analysis)
        return analysis

    async def get(self, analysis_id: uuid.UUID) -> RepositoryAnalysis | None:
        result = await self._session.execute(
            select(RepositoryAnalysis).where(RepositoryAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def get_for_project(self, project_id: uuid.UUID) -> list[RepositoryAnalysis]:
        result = await self._session.execute(
            select(RepositoryAnalysis)
            .where(RepositoryAnalysis.project_id == project_id)
            .order_by(RepositoryAnalysis.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        analysis_id: uuid.UUID,
        *,
        status: AnalysisStatus,
        progress: int | None = None,
        commit_sha: str | None = None,
    ) -> None:
        analysis = await self.get(analysis_id)
        if not analysis:
            return
        analysis.status = status
        if progress is not None:
            analysis.progress = progress
        if commit_sha is not None:
            analysis.commit_sha = commit_sha
        if status in (AnalysisStatus.CLONING,) and analysis.started_at is None:
            analysis.started_at = datetime.now(timezone.utc)
        await self._session.commit()

    async def save_result(
        self,
        analysis_id: uuid.UUID,
        *,
        analysis_result: dict[str, Any],
        primary_language: str | None,
    ) -> None:
        analysis = await self.get(analysis_id)
        if not analysis:
            return
        analysis.status = AnalysisStatus.COMPLETED
        analysis.progress = 100
        analysis.analysis_result = analysis_result
        analysis.primary_language = primary_language
        analysis.completed_at = datetime.now(timezone.utc)
        await self._session.commit()

    async def save_error(
        self,
        analysis_id: uuid.UUID,
        *,
        error_message: str,
    ) -> None:
        analysis = await self.get(analysis_id)
        if not analysis:
            return
        analysis.status = AnalysisStatus.FAILED
        analysis.error_message = error_message
        analysis.completed_at = datetime.now(timezone.utc)
        await self._session.commit()
