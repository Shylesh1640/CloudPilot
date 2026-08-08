"""DependencyChecker — evaluates dependency tree health for required vs optional services."""
from __future__ import annotations

from app.models.health import HealthStatus
from app.services.ai.schemas import InfrastructurePlan
from app.services.health.models import HealthCheckResult


class DependencyChecker:
    @staticmethod
    def evaluate_dependencies(
        service_id: str,
        plan: InfrastructurePlan,
        health_map: dict[str, HealthStatus],
    ) -> HealthCheckResult | None:
        """
        Checks health of all target dependencies of service_id.
        Returns HealthCheckResult if dependency issues are found.
        """
        deps = [d for d in plan.dependencies if d.source == service_id]
        if not deps:
            return None

        required_failures = []
        optional_failures = []

        for dep in deps:
            target_status = health_map.get(dep.target, HealthStatus.UNKNOWN)
            if target_status in (HealthStatus.UNHEALTHY, HealthStatus.FAILED):
                if dep.required:
                    required_failures.append(f"{dep.target} ({target_status})")
                else:
                    optional_failures.append(f"{dep.target} ({target_status})")

        if required_failures:
            return HealthCheckResult(
                service_id=service_id,
                check_type="CONTAINER",
                status=HealthStatus.FAILED,
                error_message=f"Required dependency failing: {', '.join(required_failures)}",
            )
        elif optional_failures:
            return HealthCheckResult(
                service_id=service_id,
                check_type="CONTAINER",
                status=HealthStatus.DEGRADED,
                error_message=f"Optional dependency degraded: {', '.join(optional_failures)}",
            )

        return None
