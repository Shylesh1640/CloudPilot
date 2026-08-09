"""Non-blocking detection loop that queues only confirmed failures."""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.deployment import DeploymentModel, DeploymentStatus
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.health_repository import HealthRepository
from app.repositories.self_healing_repository import SelfHealingRepository
from app.services.orchestrator import DockerRuntime
from app.services.self_healing.detector import FailureDetector
from app.services.self_healing.incident_manager import IncidentManager
from app.services.self_healing.worker import RecoveryWorker

logger = logging.getLogger("cloudpilot.self_healing_scheduler")


class SelfHealingScheduler:
    def __init__(self, worker: RecoveryWorker, interval_seconds: int = 5) -> None:
        self.worker, self.interval_seconds = worker, interval_seconds
        self._running = False
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.detect_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Self-healing detection cycle failed")
            await asyncio.sleep(self.interval_seconds)

    async def detect_cycle(self) -> None:
        async with AsyncSessionLocal() as session:
            ids = list((await session.execute(select(DeploymentModel.id).where(DeploymentModel.status == DeploymentStatus.RUNNING))).scalars())
            health, repository, runtime = HealthRepository(session), SelfHealingRepository(session), DockerRuntime()
            manager = IncidentManager(repository)
            for deployment_id in ids:
                deployment = await DeploymentRepository(session).get(deployment_id)
                if not deployment:
                    continue
                for service in deployment.services:
                    current_health = await health.get_or_create_service_health(service.id)
                    state = runtime.inspect_container(service.container_id or service.container_name).get("State", {}).get("Status", "unknown")
                    trigger = FailureDetector.is_confirmed(current_health, state)
                    if not trigger:
                        continue
                    severity = "CRITICAL" if len([s for s in deployment.services if s.service_id == service.service_id]) == 1 else "MEDIUM"
                    incident, created = await manager.open_or_update(deployment, service.service_id, trigger, severity)
                    if created:
                        await self.worker.enqueue(incident.id)
