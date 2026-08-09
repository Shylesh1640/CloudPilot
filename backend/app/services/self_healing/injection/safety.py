from __future__ import annotations

from app.core.config import settings
from app.models.deployment import DeploymentStatus


def validate_injection(deployment, service, scenario: str, duration_seconds: int, simulation: bool, active_count: int) -> str | None:
    if settings.is_production or not settings.FAILURE_INJECTION_ENABLED:
        return "Failure injection is disabled outside controlled test environments."
    if deployment.status != DeploymentStatus.RUNNING:
        return "Deployment is not active."
    if not service or not service.container_name.startswith("cloudpilot-"):
        return "Only CloudPilot-managed deployment services may be targeted."
    if duration_seconds > settings.FAILURE_MAX_DURATION_SECONDS:
        return f"Failure duration exceeds {settings.FAILURE_MAX_DURATION_SECONDS} seconds."
    if active_count >= settings.FAILURE_MAX_CONCURRENT_INJECTIONS:
        return "Maximum concurrent failure injections reached."
    if scenario not in {"CONTAINER_STOP", "CONTAINER_KILL", "SERVICE_FAILURE", "REPLICA_FAILURE", "HEALTH_CHECK_FAILURE"}:
        return "Failure scenario is not allowlisted."
    if scenario == "HEALTH_CHECK_FAILURE" and not simulation:
        return "Health-check failures are available only in simulation mode."
    return None
