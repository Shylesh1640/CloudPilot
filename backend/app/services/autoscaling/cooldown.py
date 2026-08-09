from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.autoscaling import ScalingPolicyModel
from app.services.autoscaling.models import ScalingAction


def cooldown_remaining(policy: ScalingPolicyModel, action: ScalingAction, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    last, seconds = (policy.last_scale_up_at, policy.scale_up_cooldown) if action == ScalingAction.SCALE_UP else (policy.last_scale_down_at, policy.scale_down_cooldown)
    if not last:
        return 0
    remaining = (last + timedelta(seconds=seconds) - now).total_seconds()
    return max(0, int(remaining))
