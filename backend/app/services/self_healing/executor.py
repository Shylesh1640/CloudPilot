"""The sole recovery component allowed to call the container runtime."""
from __future__ import annotations

from datetime import datetime, timezone

from app.models.deployment import ServiceActualState
from app.services.autoscaling.replica_manager import ReplicaManager
from app.services.self_healing.models import RecoveryAction, RecoveryDecision


class RecoveryExecutor:
    def __init__(self, session, runtime) -> None:
        self.session = session
        self.runtime = runtime

    async def execute(self, deployment, decision: RecoveryDecision) -> dict:
        records = [record for record in deployment.services if record.service_id == decision.service_id]
        if not records:
            raise ValueError("Recovery target is not a deployment service.")
        if decision.action == RecoveryAction.RESTART_CONTAINER:
            target = next((record for record in records if record.container_id == decision.target_container_id), None)
            if not target:
                raise ValueError("Recovery container is no longer managed by this service.")
            self.runtime.restart_container(target.container_id or target.container_name)
            target.actual_state, target.status = ServiceActualState.STARTING, "STARTING"
        elif decision.action == RecoveryAction.RESTART_SERVICE:
            for record in records:
                self.runtime.restart_container(record.container_id or record.container_name)
                record.actual_state, record.status = ServiceActualState.STARTING, "STARTING"
        elif decision.action == RecoveryAction.REPLACE_REPLICA:
            target = next((record for record in records if record.container_id == decision.target_container_id), None)
            if not target:
                raise ValueError("Replacement target is not managed by this service.")
            desired = target.desired_replicas
            self.runtime.remove_container(target.container_id or target.container_name)
            await self.session.delete(target)
            await self.session.commit()
            await ReplicaManager(self.session, self.runtime).reconcile(deployment, decision.service_id, desired)
        elif decision.action == RecoveryAction.RECONCILE_SERVICE:
            desired = max(record.desired_replicas for record in records)
            await ReplicaManager(self.session, self.runtime).reconcile(deployment, decision.service_id, desired)
        else:
            raise ValueError("Recovery action is not allowlisted.")
        await self.session.commit()
        return {"action": decision.action, "status": "COMPLETED", "target": decision.target_container_id, "completed_at": datetime.now(timezone.utc).isoformat()}
