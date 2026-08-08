"""DeploymentHealthManager — evaluates aggregate deployment health status."""
from __future__ import annotations

import logging
from app.models.health import HealthStatus
from app.services.ai.schemas import InfrastructurePlan

logger = logging.getLogger("cloudpilot.deployment_health")


class DeploymentHealthManager:
    @staticmethod
    def calculate_aggregate_health(
        service_statuses: dict[str, HealthStatus],
        plan: InfrastructurePlan,
    ) -> HealthStatus:
        """
        Evaluates overall deployment status based on individual service health states
        and required vs optional dependency rules.
        """
        if not service_statuses:
            return HealthStatus.UNKNOWN

        statuses = list(service_statuses.values())

        # If any service is starting, aggregate status is STARTING
        if any(s == HealthStatus.STARTING for s in statuses):
            return HealthStatus.STARTING

        service_dict = {s.id: s for s in plan.services}

        has_unhealthy_required = False
        has_degraded_optional = False

        for sid, status in service_statuses.items():
            svc = service_dict.get(sid)
            # Check if this service is required by another service
            is_required = any(d.target == sid and d.required for d in plan.dependencies) or (svc and svc.public)

            if status in (HealthStatus.UNHEALTHY, HealthStatus.FAILED):
                if is_required:
                    has_unhealthy_required = True
                else:
                    has_degraded_optional = True
            elif status == HealthStatus.DEGRADED:
                has_degraded_optional = True

        if has_unhealthy_required:
            return HealthStatus.UNHEALTHY
        elif has_degraded_optional:
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
