from __future__ import annotations

from datetime import datetime, timezone

from app.models.health import HealthStatus
from app.models.self_healing import FailureInjectionModel
from app.repositories.health_repository import HealthRepository
from app.repositories.self_healing_repository import SelfHealingRepository
from app.services.self_healing.injection.safety import validate_injection


class FailureInjectionController:
    def __init__(self, session, runtime) -> None:
        self.session, self.runtime = session, runtime
        self.repository = SelfHealingRepository(session)

    async def create(self, deployment, user_id, service, scenario: str, duration_seconds: int, simulation: bool) -> FailureInjectionModel:
        issue = validate_injection(deployment, service, scenario, duration_seconds, simulation, await self.repository.active_injections(deployment.id))
        if issue:
            raise ValueError(issue)
        injection = await self.repository.save(FailureInjectionModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=service.service_id, target_container_id=service.container_id, scenario=scenario, simulation=simulation, created_by=user_id))
        await self.repository.audit(user_id=user_id, project_id=deployment.project_id, deployment_id=deployment.id, service_id=service.service_id, action="FAILURE_INJECTED", reason=scenario, result="PENDING", metadata={"simulation": simulation})
        return injection

    async def execute(self, injection_id) -> FailureInjectionModel | None:
        injection = await self.repository.injection(injection_id)
        if not injection:
            return None
        injection.status, injection.started_at = "RUNNING", datetime.now(timezone.utc)
        await self.repository.save(injection)
        from app.repositories.deployment_repository import DeploymentRepository
        deployment = await DeploymentRepository(self.session).get(injection.deployment_id)
        records = [record for record in (deployment.services if deployment else []) if record.service_id == injection.service_id]
        try:
            if injection.simulation or injection.scenario == "HEALTH_CHECK_FAILURE":
                health = HealthRepository(self.session)
                for record in records:
                    await health.update_service_health(record.id, status=HealthStatus.FAILED, consecutive_failures=3, consecutive_successes=0, last_error="Injected simulated failure")
            elif injection.scenario == "SERVICE_FAILURE":
                for record in records:
                    self.runtime.stop_container(record.container_id or record.container_name, timeout=0)
            else:
                record = next((item for item in records if item.container_id == injection.target_container_id), None)
                if not record:
                    raise ValueError("Injection target is no longer managed.")
                # Docker's stop with zero grace period is the controlled kill-equivalent
                # exposed by the Phase 4 runtime abstraction.
                self.runtime.stop_container(record.container_id or record.container_name, timeout=0 if injection.scenario == "CONTAINER_KILL" else 10)
            injection.status, injection.completed_at = "COMPLETED", datetime.now(timezone.utc)
        except Exception:
            injection.status, injection.completed_at = "FAILED", datetime.now(timezone.utc)
        return await self.repository.save(injection)
