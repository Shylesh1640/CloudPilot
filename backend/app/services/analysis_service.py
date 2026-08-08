"""AnalysisService — manages analysis lifecycle and background execution tasks."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.models.repository_analysis import AnalysisStatus, RepositoryAnalysis
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.project_repository import ProjectRepository
from app.services.repository_analyzer import (
    RepositoryAnalysisError,
    RepositoryAnalyzer,
    clone_repository,
    parse_github_url,
)

logger = logging.getLogger("cloudpilot.analysis_service")


class AnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AnalysisRepository(session)
        self._project_repo = ProjectRepository(session)

    async def trigger_analysis(
        self,
        *,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        repository_url: str,
    ) -> RepositoryAnalysis:
        """Verify project ownership, create pending analysis DB record."""
        project = await self._project_repo.get_by_id_for_user(project_id, user_id)
        if not project:
            raise ValueError("Project not found or access denied")

        owner, repo_name = parse_github_url(repository_url)

        analysis = await self._repo.create(
            project_id=project_id,
            repository_url=repository_url,
            repository_owner=owner,
            repository_name=repo_name,
        )
        return analysis

    async def get_analysis(
        self,
        analysis_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> RepositoryAnalysis | None:
        """Get analysis record ensuring user owns the associated project."""
        analysis = await self._repo.get(analysis_id)
        if not analysis:
            return None

        project = await self._project_repo.get_by_id_for_user(analysis.project_id, user_id)
        if not project:
            return None

        return analysis


async def run_background_analysis(analysis_id: uuid.UUID) -> None:
    """
    Background worker task — clones repository, runs RepositoryAnalyzer,
    updates DB progress, and saves final profile or failure reason.
    Uses an independent DB session.
    """
    async with AsyncSessionLocal() as session:
        repo = AnalysisRepository(session)
        analysis = await repo.get(analysis_id)
        if not analysis:
            logger.error(f"Background analysis task failed: analysis_id {analysis_id} not found")
            return

        try:
            await repo.update_status(analysis_id, status=AnalysisStatus.CLONING, progress=10)

            # Shallow clone repo safely
            with clone_repository(analysis.repository_url) as (temp_dir, commit_sha):
                await repo.update_status(
                    analysis_id,
                    status=AnalysisStatus.SCANNING,
                    progress=25,
                    commit_sha=commit_sha,
                )

                analyzer = RepositoryAnalyzer()

                def progress_cb(pct: int, msg: str) -> None:
                    logger.debug(f"Analysis {analysis_id} progress: {pct}% - {msg}")

                profile = analyzer.analyze(
                    repo_dir=temp_dir,
                    repo_url=analysis.repository_url,
                    owner=analysis.repository_owner or "",
                    name=analysis.repository_name or "",
                    commit_sha=commit_sha,
                    progress_callback=progress_cb,
                )

                await repo.save_result(
                    analysis_id,
                    analysis_result=profile.to_dict(),
                    primary_language=profile.languages.primary,
                )
                logger.info(f"Background analysis {analysis_id} completed successfully")

        except RepositoryAnalysisError as err:
            logger.warning(f"Analysis {analysis_id} failed: [{err.code}] {err.message}")
            await repo.save_error(analysis_id, error_message=err.message)
        except Exception as exc:
            logger.exception(f"Unexpected error during analysis {analysis_id}: {exc}")
            await repo.save_error(
                analysis_id,
                error_message="An unexpected error occurred during repository analysis.",
            )
