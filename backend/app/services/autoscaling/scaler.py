"""Applies already-validated decisions and records observable lifecycle events."""
from __future__ import annotations

from datetime import datetime, timezone

from app.services.autoscaling.models import DecisionStatus, ScalingAction, ScalingDecision


class Autoscaler:
    def __init__(self, evaluator, replicas) -> None:
        self.evaluator = evaluator
        self.replicas = replicas

    async def apply(self, deployment, policy, decision: ScalingDecision) -> ScalingDecision:
        if decision.action not in (ScalingAction.SCALE_UP, ScalingAction.SCALE_DOWN):
            return decision
        if policy.dry_run:
            decision.status = DecisionStatus.COMPLETED
            decision.reason = f"Dry run: would change replicas from {decision.current_replicas} to {decision.recommended_replicas}."
            await self.evaluator.repository.finalize_decision(decision.record_id, decision.status, decision.reason)
            return decision
        try:
            await self.evaluator.event(deployment, decision.service_id, f"{decision.action}_STARTED", f"Scaling {decision.service_id} from {decision.current_replicas} to {decision.recommended_replicas}.")
            await self.replicas.scale_to(deployment, decision.service_id, decision.recommended_replicas)
            if decision.action == ScalingAction.SCALE_UP:
                policy.last_scale_up_at = datetime.now(timezone.utc)
            else:
                policy.last_scale_down_at = datetime.now(timezone.utc)
            await self.evaluator.repository.save_policy(policy)
            decision.status = DecisionStatus.COMPLETED
            await self.evaluator.event(deployment, decision.service_id, f"{decision.action}_COMPLETED", f"Scaled {decision.service_id} to {decision.recommended_replicas} replicas.")
        except Exception as exc:
            decision.status = DecisionStatus.FAILED
            await self.evaluator.event(deployment, decision.service_id, f"{decision.action}_FAILED", str(exc))
        await self.evaluator.repository.finalize_decision(decision.record_id, decision.status, decision.reason)
        return decision
