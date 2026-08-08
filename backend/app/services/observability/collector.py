"""MetricsCollector — scans managed containers, normalizes stats, persists to DB, and streams over WebSockets."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.database import AsyncSessionLocal
from app.models.deployment import DeploymentStatus
from app.models.observability import ContainerMetricsModel
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.observability_repository import ObservabilityRepository
from app.services.observability.docker_metrics import DockerMetricsProvider
from app.services.observability.websocket_manager import ws_manager

logger = logging.getLogger("cloudpilot.metrics_collector")


class MetricsCollector:
    def __init__(self, provider: DockerMetricsProvider | None = None) -> None:
        self.provider = provider or DockerMetricsProvider()

    async def collect_and_store_cycle(self) -> None:
        """Executes one collection cycle across all active deployments."""
        async with AsyncSessionLocal() as session:
            dep_repo = DeploymentRepository(session)
            obs_repo = ObservabilityRepository(session)

            active_statuses = [DeploymentStatus.RUNNING, DeploymentStatus.STARTING]
            from sqlalchemy import select
            from app.models.deployment import DeploymentModel
            res = await session.execute(
                select(DeploymentModel).where(DeploymentModel.status.in_(active_statuses))
            )
            deployments = res.scalars().all()

            for deployment in deployments:
                batch: list[ContainerMetricsModel] = []
                metrics_dict: dict[str, Any] = {}

                for svc in deployment.services:
                    norm = self.provider.collect_container_telemetry(
                        project_id=str(deployment.project_id),
                        deployment_id=str(deployment.id),
                        service_id=svc.service_id,
                        container_name_or_id=svc.container_name,
                    )
                    if not norm:
                        continue

                    model = ContainerMetricsModel(
                        project_id=deployment.project_id,
                        deployment_id=deployment.id,
                        service_id=svc.service_id,
                        container_id=norm.container_id,
                        timestamp=norm.timestamp,
                        cpu_percent=norm.cpu_percent,
                        memory_usage_bytes=norm.memory_usage_bytes,
                        memory_limit_bytes=norm.memory_limit_bytes,
                        memory_percent=norm.memory_percent,
                        network_rx_bytes=norm.network_rx_bytes,
                        network_tx_bytes=norm.network_tx_bytes,
                        network_rx_rate=norm.network_rx_rate,
                        network_tx_rate=norm.network_tx_rate,
                        block_read_bytes=norm.block_read_bytes,
                        block_write_bytes=norm.block_write_bytes,
                        restart_count=norm.restart_count,
                        container_state=norm.container_state,
                    )
                    batch.append(model)

                    metrics_dict[svc.service_id] = {
                        "cpu_percent": norm.cpu_percent,
                        "memory_usage_bytes": norm.memory_usage_bytes,
                        "memory_percent": norm.memory_percent,
                        "network_rx_rate": norm.network_rx_rate,
                        "network_tx_rate": norm.network_tx_rate,
                        "restart_count": norm.restart_count,
                        "container_state": norm.container_state,
                    }

                if batch:
                    await obs_repo.add_metrics_batch(batch)
                    await ws_manager.broadcast_metrics(str(deployment.id), metrics_dict)
