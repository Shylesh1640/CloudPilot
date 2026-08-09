from datetime import datetime, timezone

from app.services.autoscaling.models import MetricSnapshot, Policy, ScalingAction
from app.services.autoscaling.policies import evaluate_policy


def snapshot(**values):
    return MetricSnapshot(timestamp=datetime.now(timezone.utc), **values)


def test_cpu_replica_calculation_and_step_limit():
    decision = evaluate_policy("api", 2, snapshot(cpu_percent=140), Policy(min_replicas=1, max_replicas=5, target_cpu=70, max_scale_up_step=2))
    assert decision.action == ScalingAction.SCALE_UP
    assert decision.recommended_replicas == 4


def test_cpu_hysteresis_does_not_oscillate():
    policy = Policy(min_replicas=1, max_replicas=5, target_cpu=70)
    assert evaluate_policy("api", 2, snapshot(cpu_percent=69), policy).action == ScalingAction.NO_ACTION
    assert evaluate_policy("api", 2, snapshot(cpu_percent=29), policy).action == ScalingAction.SCALE_DOWN


def test_multi_metric_scales_up_on_any_and_down_only_on_all():
    policy = Policy(min_replicas=1, max_replicas=5, target_cpu=70, target_memory=75)
    assert evaluate_policy("api", 2, snapshot(cpu_percent=50, memory_percent=85), policy).action == ScalingAction.SCALE_UP
    assert evaluate_policy("api", 2, snapshot(cpu_percent=20, memory_percent=70), policy).action == ScalingAction.NO_ACTION


def test_request_rate_requires_no_invented_value():
    policy = Policy(target_cpu=None, target_request_rate=1000)
    decision = evaluate_policy("api", 1, snapshot(request_rate=None), policy)
    assert decision.action == ScalingAction.BLOCKED


def test_request_rate_calculates_replicas():
    policy = Policy(target_cpu=None, target_request_rate=1000, max_replicas=5)
    decision = evaluate_policy("api", 1, snapshot(request_rate=1800), policy)
    assert decision.action == ScalingAction.SCALE_UP
    assert decision.recommended_replicas == 2
