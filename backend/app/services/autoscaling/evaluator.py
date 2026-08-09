"""Coordinates deterministic policy evaluation and durable decision history."""
from __future__ import annotations

from datetime import datetime, timezone

from app.models.autoscaling import ScalingDecisionModel, ScalingEventModel, ScalingPolicyModel
from app.repositories.autoscaling_repository import AutoscalingRepository
from app.services.autoscaling.cooldown import cooldown_remaining
from app.services.autoscaling.metrics_adapter import MetricsAdapter
from app.services.autoscaling.models import DecisionStatus, MetricSnapshot, Policy, ScalingAction, ScalingDecision
from app.services.autoscaling.policies import evaluate_policy


class AutoscalingEvaluator:
    def __init__(self, repository: AutoscalingRepository, metrics: MetricsAdapter, max_metric_age_seconds: int = 30) -> None:
        self.repository = repository
        self.metrics = metrics
        self.max_metric_age_seconds = max_metric_age_seconds

    @staticmethod
    def policy_from_model(model: ScalingPolicyModel) -> Policy:
        return Policy(model.min_replicas, model.max_replicas, model.target_cpu, model.target_memory, model.target_request_rate, model.target_latency, model.scale_up_threshold, model.scale_down_threshold, model.max_scale_up_step, model.max_scale_down_step)

    async def evaluate(self, deployment, service_id: str, current_replicas: int, policy: ScalingPolicyModel, synthetic_metrics: MetricSnapshot | None = None) -> ScalingDecision:
        if not policy.enabled:
            decision = ScalingDecision(service_id, current_replicas, current_replicas, ScalingAction.NO_ACTION, "Autoscaling is disabled.")
        else:
            metrics = synthetic_metrics or await self.metrics.recent_snapshot(deployment.id, service_id, policy.stabilization_window)
            if metrics is None:
                decision = ScalingDecision(service_id, current_replicas, current_replicas, ScalingAction.BLOCKED, "Telemetry is unavailable.")
            elif (datetime.now(timezone.utc) - metrics.timestamp).total_seconds() > self.max_metric_age_seconds:
                decision = ScalingDecision(service_id, current_replicas, current_replicas, ScalingAction.BLOCKED, "Telemetry is stale.", metrics.as_dict())
            else:
                decision = evaluate_policy(service_id, current_replicas, metrics, self.policy_from_model(policy))
                if decision.action in (ScalingAction.SCALE_UP, ScalingAction.SCALE_DOWN):
                    remaining = cooldown_remaining(policy, decision.action)
                    if remaining:
                        decision = ScalingDecision(service_id, current_replicas, current_replicas, ScalingAction.BLOCKED, f"{decision.action.replace('_', ' ').title()} cooldown active for {remaining}s.", decision.metrics)
        row = ScalingDecisionModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=service_id, current_replicas=decision.current_replicas, recommended_replicas=decision.recommended_replicas, action=decision.action, status=decision.status, trigger_metric=decision.trigger_metric, metric_value=decision.metric_value, target_value=decision.target_value, reason=decision.reason, metrics_json=decision.metrics)
        await self.repository.record_decision(row)
        decision.record_id = row.id
        return decision

    async def event(self, deployment, service_id: str, event_type: str, message: str, metadata: dict | None = None) -> None:
        await self.repository.record_event(ScalingEventModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=service_id, event_type=event_type, message=message, metadata_json=metadata))
