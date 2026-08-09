from __future__ import annotations

from app.services.self_healing.models import Diagnosis, RecoveryAction, RecoveryDecision


class RecoveryPolicyEngine:
    """Least-disruptive deterministic action selector; no model or shell input."""
    @staticmethod
    def decide(diagnosis: Diagnosis, failed_container_id: str | None, replica_count: int, desired_replicas: int) -> RecoveryDecision:
        if diagnosis.failure_type == "CONTAINER_EXITED" and failed_container_id and replica_count > 1:
            return RecoveryDecision(RecoveryAction.RESTART_CONTAINER, diagnosis.root_service_id, failed_container_id, "A single managed replica exited; restart is the least disruptive action.", diagnosis.evidence)
        if replica_count < desired_replicas:
            return RecoveryDecision(RecoveryAction.RECONCILE_SERVICE, diagnosis.root_service_id, None, "Actual replicas are below desired state.", diagnosis.evidence)
        if diagnosis.failure_type in {"CONTAINER_EXITED", "SERVICE_UNHEALTHY", "DEPENDENCY_FAILED"}:
            return RecoveryDecision(RecoveryAction.RESTART_SERVICE, diagnosis.root_service_id, failed_container_id, "The root service is unavailable; restart the root service only.", diagnosis.evidence)
        return RecoveryDecision(RecoveryAction.ESCALATE, diagnosis.root_service_id, failed_container_id, "No allowed deterministic recovery action matches this failure.", diagnosis.evidence)
