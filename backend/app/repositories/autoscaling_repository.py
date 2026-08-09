"""Persistence gateway for policies, decisions, events and traffic runs."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.autoscaling import ScalingDecisionModel, ScalingEventModel, ScalingPolicyModel, TrafficRunModel


class AutoscalingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_policy(self, deployment_id: uuid.UUID, service_id: str) -> ScalingPolicyModel | None:
        result = await self.session.execute(select(ScalingPolicyModel).where(ScalingPolicyModel.deployment_id == deployment_id, ScalingPolicyModel.service_id == service_id))
        return result.scalar_one_or_none()

    async def save_policy(self, policy: ScalingPolicyModel) -> ScalingPolicyModel:
        self.session.add(policy)
        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def decisions(self, deployment_id: uuid.UUID, limit: int = 100) -> list[ScalingDecisionModel]:
        result = await self.session.execute(select(ScalingDecisionModel).where(ScalingDecisionModel.deployment_id == deployment_id).order_by(ScalingDecisionModel.created_at.desc()).limit(limit))
        return list(result.scalars())

    async def events(self, deployment_id: uuid.UUID, limit: int = 100) -> list[ScalingEventModel]:
        result = await self.session.execute(select(ScalingEventModel).where(ScalingEventModel.deployment_id == deployment_id).order_by(ScalingEventModel.created_at.desc()).limit(limit))
        return list(result.scalars())

    async def record_decision(self, decision: ScalingDecisionModel) -> ScalingDecisionModel:
        self.session.add(decision)
        await self.session.commit()
        await self.session.refresh(decision)
        return decision

    async def finalize_decision(self, decision_id: uuid.UUID | None, status: str, reason: str | None = None) -> None:
        if decision_id is None:
            return
        row = await self.session.get(ScalingDecisionModel, decision_id)
        if row:
            row.status = status
            if reason:
                row.reason = reason
            await self.session.commit()

    async def record_event(self, event: ScalingEventModel) -> ScalingEventModel:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def create_traffic_run(self, run: TrafficRunModel) -> TrafficRunModel:
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_traffic_run(self, run_id: uuid.UUID) -> TrafficRunModel | None:
        result = await self.session.execute(select(TrafficRunModel).where(TrafficRunModel.id == run_id))
        return result.scalar_one_or_none()

    async def traffic_runs(self, deployment_id: uuid.UUID, limit: int = 100) -> list[TrafficRunModel]:
        result = await self.session.execute(select(TrafficRunModel).where(TrafficRunModel.deployment_id == deployment_id).order_by(TrafficRunModel.created_at.desc()).limit(limit))
        return list(result.scalars())

    async def active_traffic_count(self, deployment_id: uuid.UUID) -> int:
        result = await self.session.execute(select(TrafficRunModel.id).where(TrafficRunModel.deployment_id == deployment_id, TrafficRunModel.status.in_(("PENDING", "RUNNING", "STOPPING"))))
        return len(list(result.scalars()))

    async def update_traffic_run(self, run: TrafficRunModel, *, status: str | None = None, current_rps: float | None = None) -> TrafficRunModel:
        if status is not None:
            run.status = status
            if status == "RUNNING" and not run.started_at:
                run.started_at = datetime.now(timezone.utc)
            if status in {"COMPLETED", "CANCELLED", "FAILED"}:
                run.completed_at = datetime.now(timezone.utc)
        if current_rps is not None:
            run.current_rps = current_rps
        await self.session.commit()
        await self.session.refresh(run)
        return run
