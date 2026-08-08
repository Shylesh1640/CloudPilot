"""High-level ObservabilityService coordinating REST metrics, logs, and events queries."""
from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.observability_repository import ObservabilityRepository
from app.repositories.project_repository import ProjectRepository
from app.services.observability.deployment_metrics import DeploymentMetricsAggregator
from app.services.observability.log_manager import LogManager
from app.services.observability.schemas import (
    ContainerMetricsRead,
    DeploymentMetricsRead,
    LogEntriesRead,
    ServiceMetricsRead,
)
from app.services.observability.service_metrics import ServiceMetricsAggregator


class ObservabilityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.dep_repo = DeploymentRepository(session)
        self.project_repo = ProjectRepository(session)
        self.obs_repo = ObservabilityRepository(session)
        self.log_manager = LogManager()

    async def _verify_ownership(self, deployment_id: uuid.UUID, user_id: uuid.UUID) -> None:
        deployment = await self.dep_repo.get(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found.")
        project = await self.project_repo.get_by_id_for_user(deployment.project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Deployment not found or access denied.")

    async def get_deployment_metrics(
        self,
        deployment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DeploymentMetricsRead:
        await self._verify_ownership(deployment_id, user_id)
        deployment = await self.dep_repo.get(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found.")

        svc_metrics: dict[str, ServiceMetricsRead] = {}
        for svc in deployment.services:
            latest = await self.obs_repo.get_latest_for_service(deployment_id, svc.service_id)
            if latest:
                svc_metrics[svc.service_id] = ServiceMetricsRead(
                    service_id=svc.service_id,
                    timestamp=latest.timestamp,
                    cpu_percent=latest.cpu_percent,
                    memory_usage_bytes=latest.memory_usage_bytes,
                    memory_limit_bytes=latest.memory_limit_bytes,
                    memory_percent=latest.memory_percent,
                    network_rx_rate=latest.network_rx_rate,
                    network_tx_rate=latest.network_tx_rate,
                    restart_count=latest.restart_count,
                    container_state=latest.container_state,
                )

        return DeploymentMetricsAggregator.aggregate(deployment_id, svc_metrics)

    async def get_service_current_metrics(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
        user_id: uuid.UUID,
    ) -> ServiceMetricsRead:
        await self._verify_ownership(deployment_id, user_id)
        latest = await self.obs_repo.get_latest_for_service(deployment_id, service_id)
        if not latest:
            return ServiceMetricsRead(
                service_id=service_id,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                cpu_percent=0.0,
                memory_usage_bytes=0,
                memory_limit_bytes=None,
                memory_percent=0.0,
                network_rx_rate=0.0,
                network_tx_rate=0.0,
                restart_count=0,
                container_state="unknown",
            )

        return ServiceMetricsRead(
            service_id=service_id,
            timestamp=latest.timestamp,
            cpu_percent=latest.cpu_percent,
            memory_usage_bytes=latest.memory_usage_bytes,
            memory_limit_bytes=latest.memory_limit_bytes,
            memory_percent=latest.memory_percent,
            network_rx_rate=latest.network_rx_rate,
            network_tx_rate=latest.network_tx_rate,
            restart_count=latest.restart_count,
            container_state=latest.container_state,
        )

    async def get_service_metrics_history(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
        user_id: uuid.UUID,
        minutes: int = 15,
        limit: int = 200,
    ) -> list[ContainerMetricsRead]:
        await self._verify_ownership(deployment_id, user_id)
        start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=minutes)
        records = await self.obs_repo.get_service_history(deployment_id, service_id, start_time=start_time, limit=limit)
        return [ContainerMetricsRead.model_validate(r) for r in records]

    async def get_container_logs(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
        user_id: uuid.UUID,
        tail: int = 100,
        level_filter: str | None = None,
        search_term: str | None = None,
    ) -> LogEntriesRead:
        await self._verify_ownership(deployment_id, user_id)
        deployment = await self.dep_repo.get(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found.")

        svc = next((s for s in deployment.services if s.service_id == service_id), None)
        if not svc:
            raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found in deployment.")

        return self.log_manager.get_container_logs(
            service_id=service_id,
            container_name_or_id=svc.container_name,
            tail=tail,
            level_filter=level_filter,
            search_term=search_term,
        )
