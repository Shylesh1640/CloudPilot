"""HealthScheduler — background task runner scheduling concurrent health check loops."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.database import AsyncSessionLocal
from app.models.deployment import DeploymentStatus
from app.models.health import HealthStatus
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.health_repository import HealthRepository
from app.repositories.plan_repository import PlanRepository
from app.services.ai.schemas import InfrastructurePlan
from app.services.health.deployment_health import DeploymentHealthManager
from app.services.health.events import HealthEventManager
from app.services.health.flapping_detector import FlappingDetector
from app.services.health.health_checker import HealthChecker
from app.services.health.policies import DEFAULT_HEALTH_POLICY, HealthPolicy

logger = logging.getLogger("cloudpilot.health_scheduler")


class HealthScheduler:
    """Schedules periodic concurrent health checks for all active deployments."""

    def __init__(self, policy: HealthPolicy | None = None) -> None:
        self.policy = policy or DEFAULT_HEALTH_POLICY
        self.checker = HealthChecker()
        self.flapping_detector = FlappingDetector(self.policy)
        self._task: asyncio.Task | None = None
        self._running = False

    def start() -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("HealthScheduler background loop started.")

    def stop() -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("HealthScheduler background loop stopped.")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self.run_health_check_cycle()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception(f"Error in HealthScheduler cycle: {exc}")

            await asyncio.sleep(self.policy.check_interval_seconds)

    async def run_health_check_cycle(self) -> None:
        """Runs one check cycle for all active deployments."""
        async with AsyncSessionLocal() as session:
            dep_repo = DeploymentRepository(session)
            plan_repo = PlanRepository(session)
            health_repo = HealthRepository(session)

            # Find active running deployments
            active_statuses = [DeploymentStatus.RUNNING, DeploymentStatus.STARTING]
            result = await session.execute(
                DeploymentRepository._session.select(dep_repo._session) if False else None
            ) if False else None

            # Fetch deployments directly via query
            from sqlalchemy import select
            from app.models.deployment import DeploymentModel
            res = await session.execute(
                select(DeploymentModel).where(DeploymentModel.status.in_(active_statuses))
            )
            deployments = res.scalars().all()

            for deployment in deployments:
                plan_rec = await plan_repo.get(deployment.infrastructure_plan_id)
                if not plan_rec or not plan_rec.plan_data:
                    continue

                plan = InfrastructurePlan.model_validate(plan_rec.plan_data)
                event_mgr = HealthEventManager(health_repo)

                service_health_map: dict[str, HealthStatus] = {}

                for svc in deployment.services:
                    plan_svc = next((s for s in plan.services if s.id == svc.service_id), None)
                    if not plan_svc:
                        continue

                    # Current health record
                    current_health = await health_repo.get_or_create_service_health(svc.id)
                    prev_status = current_health.status

                    # Check grace period
                    now = datetime.datetime.now(datetime.timezone.utc) if 'datetime' in locals() else __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
                    start_time = deployment.started_at or deployment.created_at
                    elapsed = (now - start_time).total_seconds()

                    if elapsed < self.policy.startup_grace_period_seconds:
                        new_status = HealthStatus.STARTING
                        await health_repo.update_service_health(
                            svc.id,
                            status=new_status,
                            consecutive_failures=0,
                            consecutive_successes=0,
                        )
                        service_health_map[svc.service_id] = new_status
                        continue

                    # Execute check
                    hc_res = await self.checker.check_service_health(
                        service=plan_svc,
                        container_name=svc.container_name,
                        network_host_alias=svc.service_id,
                        health_check_port=svc.port,
                    )

                    # Update thresholds
                    if hc_res.status in (HealthStatus.HEALTHY, HealthStatus.STARTING):
                        new_failures = 0
                        new_successes = current_health.consecutive_successes + 1
                        if new_successes >= self.policy.success_threshold:
                            new_status = HealthStatus.HEALTHY
                        else:
                            new_status = current_health.status
                    else:
                        new_successes = 0
                        new_failures = current_health.consecutive_failures + 1
                        if new_failures >= self.policy.failure_threshold:
                            new_status = HealthStatus.UNHEALTHY
                        else:
                            new_status = current_health.status

                    # Check flapping
                    if self.flapping_detector.record_and_check_flapping(svc.service_id, new_status):
                        new_status = HealthStatus.DEGRADED
                        await event_mgr.emit_flapping_event(deployment.project_id, deployment.id, svc.service_id)

                    # Record check log
                    await health_repo.add_check_record(
                        deployment_service_id=svc.id,
                        check_type=hc_res.check_type,
                        status=hc_res.status,
                        latency_ms=hc_res.latency_ms,
                        status_code=hc_res.status_code,
                        error_message=hc_res.error_message,
                        retention_limit=self.policy.history_retention_limit,
                    )

                    # Update current state
                    await health_repo.update_service_health(
                        svc.id,
                        status=new_status,
                        consecutive_failures=new_failures,
                        consecutive_successes=new_successes,
                        latency_ms=hc_res.latency_ms,
                        last_error=hc_res.error_message,
                    )

                    # Emit transition event
                    await event_mgr.emit_state_transition(
                        project_id=deployment.project_id,
                        deployment_id=deployment.id,
                        service_id=svc.service_id,
                        previous_state=prev_status,
                        new_state=new_status,
                    )

                    service_health_map[svc.service_id] = new_status

                # Calculate Aggregate Deployment Health
                overall_health = DeploymentHealthManager.calculate_aggregate_health(service_health_map, plan)
                if overall_health == HealthStatus.HEALTHY and deployment.status != DeploymentStatus.RUNNING:
                    await dep_repo.update_status(deployment.id, status=DeploymentStatus.RUNNING, log_entry="Deployment is READY and HEALTHY.")
