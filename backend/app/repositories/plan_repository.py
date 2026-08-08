"""Database access layer for infrastructure plans."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.infrastructure_plan import InfrastructurePlanModel, PlanStatus


class PlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        project_id: uuid.UUID,
        repository_analysis_id: uuid.UUID,
        version: int = 1,
        ai_provider: str | None = None,
        ai_model: str | None = None,
    ) -> InfrastructurePlanModel:
        plan = InfrastructurePlanModel(
            project_id=project_id,
            repository_analysis_id=repository_analysis_id,
            version=version,
            status=PlanStatus.PENDING,
            ai_provider=ai_provider,
            ai_model=ai_model,
        )
        self._session.add(plan)
        await self._session.commit()
        await self._session.refresh(plan)
        return plan

    async def get(self, plan_id: uuid.UUID) -> InfrastructurePlanModel | None:
        result = await self._session.execute(
            select(InfrastructurePlanModel).where(InfrastructurePlanModel.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_project(self, project_id: uuid.UUID) -> InfrastructurePlanModel | None:
        result = await self._session.execute(
            select(InfrastructurePlanModel)
            .where(InfrastructurePlanModel.project_id == project_id)
            .order_by(InfrastructurePlanModel.version.desc(), InfrastructurePlanModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        plan_id: uuid.UUID,
        *,
        status: PlanStatus,
    ) -> None:
        plan = await self.get(plan_id)
        if not plan:
            return
        plan.status = status
        await self._session.commit()

    async def save_result(
        self,
        plan_id: uuid.UUID,
        *,
        plan_data: dict[str, Any],
        validation_result: dict[str, Any],
        duration_ms: int,
        ai_provider: str | None = None,
        ai_model: str | None = None,
    ) -> None:
        plan = await self.get(plan_id)
        if not plan:
            return
        plan.status = PlanStatus.COMPLETED
        plan.plan_data = plan_data
        plan.validation_result = validation_result
        plan.generation_duration_ms = duration_ms
        if ai_provider:
            plan.ai_provider = ai_provider
        if ai_model:
            plan.ai_model = ai_model
        await self._session.commit()

    async def save_error(
        self,
        plan_id: uuid.UUID,
        *,
        error_message: str,
    ) -> None:
        plan = await self.get(plan_id)
        if not plan:
            return
        plan.status = PlanStatus.FAILED
        plan.error_message = error_message
        await self._session.commit()
