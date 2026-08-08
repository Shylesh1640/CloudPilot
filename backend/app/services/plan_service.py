"""PlanService — handles API requests and background plan generation tasks."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.infrastructure_plan import InfrastructurePlanModel, PlanStatus
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.project_repository import ProjectRepository
from app.services.ai import AIArchitecturePlanner, AIPlannerError

logger = logging.getLogger("cloudpilot.plan_service")


class PlanService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._plan_repo = PlanRepository(session)
        self._analysis_repo = AnalysisRepository(session)
        self._project_repo = ProjectRepository(session)

    async def trigger_plan_generation(
        self,
        *,
        analysis_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> InfrastructurePlanModel:
        """Verify analysis existence and project ownership, create pending plan DB record."""
        analysis = await self._analysis_repo.get(analysis_id)
        if not analysis:
            raise ValueError("Repository analysis record not found.")

        project = await self._project_repo.get_by_id_for_user(analysis.project_id, user_id)
        if not project:
            raise ValueError("Project not found or access denied.")

        if analysis.status != "COMPLETED" or not analysis.analysis_result:
            raise ValueError("Repository analysis must be COMPLETED before generating an infrastructure plan.")

        # Check existing version
        latest = await self._plan_repo.get_latest_for_project(analysis.project_id)
        next_version = (latest.version + 1) if latest else 1

        plan = await self._plan_repo.create(
            project_id=analysis.project_id,
            repository_analysis_id=analysis_id,
            version=next_version,
            ai_provider=settings.AI_PROVIDER,
            ai_model=settings.AI_MODEL,
        )
        return plan

    async def regenerate_plan(
        self,
        *,
        plan_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> InfrastructurePlanModel:
        """Trigger a new plan version generation for an existing plan."""
        current_plan = await self.get_plan(plan_id, user_id)
        if not current_plan:
            raise ValueError("Plan record not found or access denied.")

        return await self.trigger_plan_generation(
            analysis_id=current_plan.repository_analysis_id,
            user_id=user_id,
        )

    async def get_plan(
        self,
        plan_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> InfrastructurePlanModel | None:
        """Get plan record ensuring user owns the associated project."""
        plan = await self._plan_repo.get(plan_id)
        if not plan:
            return None

        project = await self._project_repo.get_by_id_for_user(plan.project_id, user_id)
        if not project:
            return None

        return plan


async def run_background_planning(plan_id: uuid.UUID) -> None:
    """
    Background worker task — loads RepositoryProfile, invokes AIArchitecturePlanner,
    updates DB progress, and saves final validated InfrastructurePlan.
    """
    async with AsyncSessionLocal() as session:
        plan_repo = PlanRepository(session)
        analysis_repo = AnalysisRepository(session)

        plan = await plan_repo.get(plan_id)
        if not plan:
            logger.error(f"Background planning task failed: plan_id {plan_id} not found")
            return

        analysis = await analysis_repo.get(plan.repository_analysis_id)
        if not analysis or not analysis.analysis_result:
            await plan_repo.save_error(plan_id, error_message="Repository analysis result unavailable.")
            return

        try:
            await plan_repo.update_status(plan_id, status=PlanStatus.GENERATING)

            planner = AIArchitecturePlanner()
            await plan_repo.update_status(plan_id, status=PlanStatus.VALIDATING)

            plan_obj, validation_res, duration_ms = await planner.plan_architecture(analysis.analysis_result)

            await plan_repo.save_result(
                plan_id,
                plan_data=plan_obj.model_dump(mode="json"),
                validation_result=validation_res,
                duration_ms=duration_ms,
                ai_provider=settings.AI_PROVIDER,
                ai_model=settings.AI_MODEL,
            )
            logger.info(f"Background infrastructure plan {plan_id} completed successfully in {duration_ms}ms")

        except AIPlannerError as err:
            logger.warning(f"Infrastructure planning {plan_id} failed: [{err.code}] {err.message}")
            await plan_repo.save_error(plan_id, error_message=err.message)
        except Exception as exc:
            logger.exception(f"Unexpected error during plan generation {plan_id}: {exc}")
            await plan_repo.save_error(
                plan_id,
                error_message="An unexpected error occurred during AI architecture planning.",
            )
