"""Threshold evaluation and replica arithmetic.  No LLM participates here."""
from __future__ import annotations

import math

from app.services.autoscaling.models import MetricSnapshot, Policy, ScalingAction, ScalingDecision


def _thresholds(policy: Policy, metric: str) -> tuple[float, float] | None:
    target = getattr(policy, f"target_{metric}")
    if target is None:
        return None
    if metric == "cpu":
        return policy.scale_up_threshold or target, policy.scale_down_threshold or target * 0.5
    if metric == "memory":
        return policy.scale_up_threshold or max(target, target + 5), policy.scale_down_threshold or target * 0.5
    if metric == "latency":
        return target, target * 0.6
    return target, target * 0.5


def evaluate_policy(service_id: str, current_replicas: int, metrics: MetricSnapshot, policy: Policy) -> ScalingDecision:
    """Apply ANY-up / ALL-down hysteresis and bounded horizontal scaling."""
    policy.validate()
    values = {"cpu": metrics.cpu_percent, "memory": metrics.memory_percent, "request_rate": metrics.request_rate, "latency": metrics.p95_latency}
    configured = [(name, val, _thresholds(policy, name)) for name, val in values.items()]
    configured = [(name, val, thresholds) for name, val, thresholds in configured if thresholds is not None]
    missing = [name for name, value, _ in configured if value is None]
    if missing:
        return ScalingDecision(service_id, current_replicas, current_replicas, ScalingAction.BLOCKED, f"Required metrics unavailable: {', '.join(missing)}.", metrics.as_dict())
    if not configured:
        return ScalingDecision(service_id, current_replicas, current_replicas, ScalingAction.BLOCKED, "No scaling metric is configured.", metrics.as_dict())

    up_candidates: list[tuple[str, float, float, int]] = []
    down_ok = True
    for name, value, thresholds in configured:
        assert value is not None and thresholds is not None
        up, down = thresholds
        if name == "request_rate":
            desired = math.ceil(value / up) if up else current_replicas
            is_up = value > up * current_replicas
            is_down = value < up * max(current_replicas - 1, 1)
        else:
            desired = math.ceil(current_replicas * value / up) if up else current_replicas
            is_up = value > up
            is_down = value < down
        if is_up:
            up_candidates.append((name, value, up, desired))
        down_ok = down_ok and is_down

    if up_candidates:
        name, value, target, desired = max(up_candidates, key=lambda item: item[3])
        target_replicas = min(policy.max_replicas, max(current_replicas + 1, min(desired, current_replicas + policy.max_scale_up_step)))
        return ScalingDecision(service_id, current_replicas, target_replicas, ScalingAction.SCALE_UP, f"{name} exceeded the configured scale-up threshold.", metrics.as_dict(), name, value, target)
    if down_ok and current_replicas > policy.min_replicas:
        target_replicas = max(policy.min_replicas, current_replicas - policy.max_scale_down_step)
        return ScalingDecision(service_id, current_replicas, target_replicas, ScalingAction.SCALE_DOWN, "All configured metrics are below their scale-down thresholds.", metrics.as_dict())
    return ScalingDecision(service_id, current_replicas, current_replicas, ScalingAction.NO_ACTION, "Metrics are within the hysteresis range.", metrics.as_dict())
