from __future__ import annotations

from app.models.deployment import DeploymentStatus


def validate_scaling_target(deployment, service_id: str, scalable: bool, replicas: int, minimum: int, maximum: int) -> str | None:
    if deployment.status != DeploymentStatus.RUNNING:
        return "Deployment is not active."
    if not scalable:
        return f"Service '{service_id}' is not marked scalable in the infrastructure plan."
    if replicas < minimum or replicas > maximum:
        return f"Replica count must be between {minimum} and {maximum}."
    return None
