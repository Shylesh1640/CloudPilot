from __future__ import annotations

from datetime import datetime, timezone

from app.models.deployment import DeploymentStatus
from app.services.self_healing.models import RecoveryAction

ALLOWED_ACTIONS = {RecoveryAction.RESTART_CONTAINER, RecoveryAction.REPLACE_REPLICA, RecoveryAction.RESTART_SERVICE, RecoveryAction.RECONCILE_SERVICE}


def validate_recovery(deployment, policy, action: RecoveryAction, attempts: int) -> str | None:
    if deployment.status != DeploymentStatus.RUNNING:
        return "Deployment is not active."
    if not policy.enabled:
        return "Automatic recovery is disabled by policy."
    if action not in ALLOWED_ACTIONS:
        return "Recovery action is not allowlisted."
    if attempts >= policy.max_attempts:
        return "Recovery attempt limit reached."
    if policy.last_recovery_at and (datetime.now(timezone.utc) - policy.last_recovery_at).total_seconds() < policy.cooldown_seconds:
        return "Recovery cooldown is active."
    return None
