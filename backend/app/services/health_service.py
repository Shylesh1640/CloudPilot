"""High-level HealthService coordinating health check execution and API responses."""
from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health import HealthStatus
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.health_repository import HealthRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.project_repository import ProjectRepository
from app.services.ai.schemas import InfrastructurePlan
from app.services.health.deployment_health import DeploymentHealthManager
from app.services.health.events import HealthEventManager
from app.services.health.health_checker import HealthChecker
from app.services.health.policies import DEFAULT_HEALTH_POLICY
from app.services.health.schemas import (
    DeploymentHealthRead,
    HealthCheckRecordRead,
    HealthEventRead,
    ServiceHealthRead,
)


class HealthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.dep_repo = DeploymentRepository(session)
        self.plan_repo = PlanRepository(session)
        self.project_repo = ProjectRepository(session)
        self.health_repo = HealthRepository(session)
        self.checker = HealthChecker()
        self.policy = DEFAULT_HEALTH_POLICY

    async def _verify_ownership(self, deployment_id: uuid.UUID, user_id: uuid.UUID) -> DeploymentModel:
        deployment = await self.dep_repo.get(deployment_id)
        if not deployment:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Deployment not found.")
        project = await self.project_repo.get_by_id_for_user(deployment.project_id, user_id)
        if not project:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Deployment not found or access denied.")
        return deployment

    async def get_deployment_health(
        self,
        deployment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DeploymentHealthRead:
        deployment = await self._verify_ownership(deployment_id, user_id)
        plan_rec = await self.plan_repo.get(deployment.infrastructure_plan_id)
        if not plan_rec or not plan_rec.plan_data:
            plan = InfrastructurePlan(
                plan_version="1.0",
                analyzer_version="2.0",
                planner_version="1.0",
                application={"name": "app", "architecture_type": "single_service"},
                services=[],
                networks=[],
                volumes=[],
                dependencies=[],
                environment=[],
                scaling=[],
                health_checks=[],
                resource_profiles=[],
                risks=[],
                graph={"nodes": [], "edges": []},
                explanation={"summary": "", "architecture_choice": "", "scaling_reasoning": "", "security_notes": ""},
                deployment_order=[],
            )
        else:
            plan = InfrastructurePlan.model_validate(plan_rec.plan_data)

        services_health_map: dict[str, HealthStatus] = {}
        latencies: list[int] = []

        for svc in deployment.services:
            h = await self.health_repo.get_or_create_service_health(svc.id)
            services_health_map[svc.service_id] = h.status
            if h.latency_ms is not None:
                latencies.append(h.latency_ms)

        overall = DeploymentHealthManager.calculate_aggregate_health(services_health_map, plan)
        avg_lat = int(sum(latencies) / len(latencies)) if latencies else None

        return DeploymentHealthRead(
            deployment_id=deployment_id,
            status=overall,
            overall_health=overall,
            services=services_health_map,
            avg_latency_ms=avg_lat,
        )

    async def get_service_health(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
        user_id: uuid.UUID,
    ) -> ServiceHealthRead:
        deployment = await self._verify_ownership(deployment_id, user_id)
        svc = next((s for s in deployment.services if s.service_id == service_id), None)
        if not svc:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found in deployment.")

        health_rec = await self.health_repo.get_or_create_service_health(svc.id)
        return ServiceHealthRead(
            id=health_rec.id,
            deployment_service_id=svc.id,
            service_id=service_id,
            status=health_rec.status,
            consecutive_failures=health_rec.consecutive_failures,
            consecutive_successes=health_rec.consecutive_successes,
            latency_ms=health_rec.latency_ms,
            last_check_at=health_rec.last_check_at,
            last_success_at=health_rec.last_success_at,
            last_failure_at=health_rec.last_failure_at,
            last_error=health_rec.last_error,
            updated_at=health_rec.updated_at,
        )

    async def get_service_health_history(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
        user_id: uuid.UUID,
        limit: int = 100,
    ) -> list[HealthCheckRecordRead]:
        deployment = await self._verify_ownership(deployment_id, user_id)
        svc = next((s for s in deployment.services if s.service_id == service_id), None)
        if not svc:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found in deployment.")

        records = await self.health_repo.get_check_history(svc.id, limit=limit)
        return [HealthCheckRecordRead.model_validate(r) for r in records]

    async def get_deployment_events(
        self,
        deployment_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[HealthEventRead]:
        await self._verify_ownership(deployment_id, user_id)
        events = await self.health_repo.get_deployment_events(deployment_id, limit=limit)
        return [HealthEventRead.model_validate(e) for e in events]
