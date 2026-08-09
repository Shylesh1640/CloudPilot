from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.deployment import DeploymentModel
from app.models.infrastructure_plan import InfrastructurePlanModel
from app.models.self_healing import RecoveryAttemptModel, RecoveryPolicyModel
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.health_repository import HealthRepository
from app.repositories.self_healing_repository import SelfHealingRepository
from app.services.orchestrator import DockerRuntime
from app.services.self_healing.classifier import FailureClassifier
from app.services.self_healing.executor import RecoveryExecutor
from app.services.self_healing.policy_engine import RecoveryPolicyEngine
from app.services.self_healing.models import RecoveryAction, RecoveryDecision
from app.services.self_healing.retry import backoff_seconds
from app.services.self_healing.safety import validate_recovery
from app.services.self_healing.verifier import RecoveryVerifier

logger = logging.getLogger("cloudpilot.recovery_worker")


class RecoveryWorker:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[uuid.UUID] = asyncio.Queue()
        self._locks: defaultdict[tuple[str, str], asyncio.Lock] = defaultdict(asyncio.Lock)
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        if not self._running:
            self._running, self._task = True, asyncio.create_task(self._run())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def enqueue(self, incident_id: uuid.UUID) -> None:
        await self._queue.put(incident_id)

    async def _run(self) -> None:
        while self._running:
            try:
                await self.process(await self._queue.get())
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Recovery worker failed to process incident")

    async def process(self, incident_id: uuid.UUID) -> None:
        async with AsyncSessionLocal() as session:
            repo = SelfHealingRepository(session)
            incident = await repo.incident(incident_id)
            if not incident or incident.status in {"RESOLVED", "ESCALATED"}:
                return
            deployment = await DeploymentRepository(session).get(incident.deployment_id)
            if not deployment:
                return
            lock = self._locks[(str(deployment.id), incident.service_id)]
            if lock.locked():
                await repo.event(incident.id, "RECOVERY_ALREADY_RUNNING", "A recovery lock is already held for this service.")
                return
            async with lock:
                await self._recover(session, repo, deployment, incident)

    async def _recover(self, session, repo, deployment, incident) -> None:
        request_metadata = dict(incident.diagnosis or {})
        plan = await session.get(InfrastructurePlanModel, deployment.infrastructure_plan_id)
        plan_data = plan.plan_data if plan and plan.plan_data else {"dependencies": []}
        records = [record for record in deployment.services if record.service_id == incident.service_id]
        if not records:
            await repo.update_incident(incident, "ESCALATED")
            return
        health_repo = HealthRepository(session)
        health = {}
        for record in deployment.services:
            health[record.service_id] = (await health_repo.get_or_create_service_health(record.id)).status.value
        runtime = DockerRuntime()
        failed = next((record for record in records if runtime.inspect_container(record.container_id or record.container_name).get("State", {}).get("Status", "").lower() in {"exited", "dead"}), records[0])
        diagnosis = FailureClassifier.diagnose(incident.service_id, runtime.inspect_container(failed.container_id or failed.container_name).get("State", {}).get("Status", "unknown"), health, plan_data)
        incident.status, incident.root_cause_service_id, incident.root_cause_type = "INVESTIGATING", diagnosis.root_service_id, diagnosis.failure_type
        incident.diagnosis = {"root_service": diagnosis.root_service_id, "impacted_services": diagnosis.impacted_services, "evidence": diagnosis.evidence, **{key: request_metadata[key] for key in ("manual_action", "dry_run") if key in request_metadata}}
        await repo.save(incident)
        await repo.event(incident.id, "DIAGNOSIS_COMPLETED", diagnosis.failure_type, incident.diagnosis)
        target_records = [record for record in deployment.services if record.service_id == diagnosis.root_service_id]
        desired = max((record.desired_replicas for record in target_records), default=1)
        decision = RecoveryPolicyEngine.decide(diagnosis, failed.container_id, len(target_records), desired)
        requested_action = request_metadata.get("manual_action")
        if requested_action:
            try:
                action = RecoveryAction(requested_action)
            except ValueError:
                await repo.event(incident.id, "RECOVERY_ESCALATED", "Manual recovery requested a non-allowlisted action.")
                await repo.update_incident(incident, "ESCALATED")
                return
            decision = RecoveryDecision(action, diagnosis.root_service_id, failed.container_id, "User requested an allowlisted manual recovery action.", diagnosis.evidence)
        policy = await repo.policy(deployment.id, diagnosis.root_service_id)
        if not policy:
            policy = await repo.save(RecoveryPolicyModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=diagnosis.root_service_id, max_attempts=settings.RECOVERY_MAX_ATTEMPTS, cooldown_seconds=settings.RECOVERY_COOLDOWN_SECONDS, verification_timeout_seconds=settings.RECOVERY_TIMEOUT_SECONDS))
        attempts = await repo.attempts(incident.id)
        issue = validate_recovery(deployment, policy, decision.action, len(attempts))
        if issue:
            await repo.event(incident.id, "RECOVERY_ESCALATED", issue)
            await repo.update_incident(incident, "ESCALATED")
            return
        attempt = await repo.save(RecoveryAttemptModel(incident_id=incident.id, action=decision.action, target_service_id=decision.service_id, target_container_id=decision.target_container_id, attempt_number=len(attempts) + 1, status="EXECUTING", reason=decision.reason, started_at=datetime.now(timezone.utc)))
        await repo.update_incident(incident, "RECOVERING")
        await repo.event(incident.id, "RECOVERY_ACTION_SELECTED", decision.reason, {"action": decision.action})
        if policy.dry_run or bool(request_metadata.get("dry_run")):
            attempt.status, attempt.completed_at = "COMPLETED", datetime.now(timezone.utc)
            await repo.save(attempt)
            await repo.event(incident.id, "RECOVERY_DRY_RUN", f"Would execute {decision.action} without runtime changes.")
            return
        try:
            result = await RecoveryExecutor(session, runtime).execute(deployment, decision)
            attempt.status, attempt.completed_at = "COMPLETED", datetime.now(timezone.utc)
            await repo.save(attempt)
            await repo.event(incident.id, "RECOVERY_ACTION_EXECUTED", str(result))
            await repo.update_incident(incident, "VERIFYING")
            verified, message = await RecoveryVerifier(session, runtime).wait_for_service(deployment, diagnosis.root_service_id, policy.verification_timeout_seconds)
            if verified:
                policy.last_recovery_at = datetime.now(timezone.utc)
                await repo.save(policy)
                await repo.event(incident.id, "RECOVERY_VERIFIED", message)
                await repo.update_incident(incident, "RESOLVED", resolved=True)
                await repo.audit(user_id=None, project_id=deployment.project_id, deployment_id=deployment.id, service_id=diagnosis.root_service_id, action="RECOVERY_EXECUTED", reason=decision.reason, result="COMPLETED")
            else:
                raise RuntimeError(message)
        except Exception as exc:
            attempt.status, attempt.error_message, attempt.completed_at = "FAILED", str(exc), datetime.now(timezone.utc)
            await repo.save(attempt)
            now_attempts = len(await repo.attempts(incident.id))
            if now_attempts >= policy.max_attempts:
                await repo.event(incident.id, "RECOVERY_LOOP_DETECTED", "Recovery attempts exhausted; automatic recovery stopped.")
                await repo.update_incident(incident, "ESCALATED")
            else:
                await repo.event(incident.id, "RECOVERY_ACTION_FAILED", str(exc))
                await repo.update_incident(incident, "OPEN")
                asyncio.create_task(self._requeue_after(incident.id, backoff_seconds(now_attempts)))

    async def _requeue_after(self, incident_id: uuid.UUID, delay: int) -> None:
        await asyncio.sleep(delay)
        await self.enqueue(incident_id)
