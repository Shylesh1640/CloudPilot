"""Periodic, bounded autoscaling evaluations (default every ten seconds)."""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.autoscaling import ScalingPolicyModel
from app.models.infrastructure_plan import InfrastructurePlanModel
from app.repositories.autoscaling_repository import AutoscalingRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.observability_repository import ObservabilityRepository
from app.services.autoscaling.evaluator import AutoscalingEvaluator
from app.services.autoscaling.metrics_adapter import MetricsAdapter
from app.services.autoscaling.replica_manager import ReplicaManager
from app.services.autoscaling.safety import validate_scaling_target
from app.services.autoscaling.scaler import Autoscaler
from app.services.orchestrator import DockerRuntime

logger = logging.getLogger("cloudpilot.autoscaling_scheduler")


class AutoscalingScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self.evaluate_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Autoscaling evaluation cycle failed")
            await asyncio.sleep(settings.AUTOSCALING_INTERVAL_SECONDS)

    async def evaluate_cycle(self) -> None:
        async with AsyncSessionLocal() as session:
            policies = list((await session.execute(select(ScalingPolicyModel).where(ScalingPolicyModel.enabled.is_(True)))).scalars())
            repo = AutoscalingRepository(session)
            evaluator = AutoscalingEvaluator(repo, MetricsAdapter(ObservabilityRepository(session)), settings.AUTOSCALING_MAX_METRIC_AGE_SECONDS)
            for policy in policies:
                deployment = await DeploymentRepository(session).get(policy.deployment_id)
                if not deployment:
                    continue
                plan = await session.get(InfrastructurePlanModel, deployment.infrastructure_plan_id)
                definition = next((service for service in ((plan.plan_data or {}).get("services", []) if plan else []) if service.get("id") == policy.service_id), None)
                manager = ReplicaManager(session, DockerRuntime())
                current = await manager.get_current_replicas(deployment.id, policy.service_id)
                issue = validate_scaling_target(deployment, policy.service_id, bool(definition and definition.get("scalable")), current, policy.min_replicas, policy.max_replicas)
                if issue:
                    await evaluator.event(deployment, policy.service_id, "SCALING_BLOCKED", issue)
                    continue
                decision = await evaluator.evaluate(deployment, policy.service_id, current, policy)
                await Autoscaler(evaluator, manager).apply(deployment, policy, decision)
