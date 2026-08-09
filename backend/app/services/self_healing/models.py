from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class FailureScenario(StrEnum):
    CONTAINER_STOP = "CONTAINER_STOP"
    CONTAINER_KILL = "CONTAINER_KILL"
    SERVICE_FAILURE = "SERVICE_FAILURE"
    REPLICA_FAILURE = "REPLICA_FAILURE"
    HEALTH_CHECK_FAILURE = "HEALTH_CHECK_FAILURE"


class RecoveryAction(StrEnum):
    RESTART_CONTAINER = "RESTART_CONTAINER"
    REPLACE_REPLICA = "REPLACE_REPLICA"
    RESTART_SERVICE = "RESTART_SERVICE"
    RECONCILE_SERVICE = "RECONCILE_SERVICE"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class Diagnosis:
    service_id: str
    failure_type: str
    root_service_id: str
    impacted_services: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RecoveryDecision:
    action: RecoveryAction
    service_id: str
    target_container_id: str | None
    reason: str
    evidence: list[str]
