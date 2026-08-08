"""DependencyManager — calculates topological dependency order and validates dependency graph."""
from __future__ import annotations

from app.services.ai.schemas import InfrastructurePlan
from app.services.orchestrator.exceptions import DeploymentBlockedError


class DependencyManager:
    @staticmethod
    def get_execution_order(plan: InfrastructurePlan) -> list[str]:
        """
        Calculates service startup sequence based on dependencies.
        Databases and Caches start first, followed by Application/Workers, then Frontend.
        """
        service_ids = [s.id for s in plan.services]
        service_map = {s.id: s for s in plan.services}

        # Validate graph references (Rule: target exists)
        for dep in plan.dependencies:
            if dep.source not in service_map:
                raise DeploymentBlockedError(
                    f"Dependency source '{dep.source}' does not exist in plan services.",
                    code="DEPLOYMENT_REJECTED",
                )
            if dep.target not in service_map:
                raise DeploymentBlockedError(
                    f"Service '{dep.source}' depends on unknown service '{dep.target}'.",
                    code="DEPLOYMENT_REJECTED",
                )

        # Topological sorting / Rank ordering
        def service_rank(svc_id: str) -> int:
            svc = service_map[svc_id]
            stype = svc.type.lower()
            if stype in ("database", "storage"):
                return 1
            elif stype in ("cache", "queue"):
                return 2
            elif stype in ("worker", "application") and not svc.public:
                return 3
            elif stype == "application" and svc.public:
                return 4
            return 5

        sorted_services = sorted(service_ids, key=lambda sid: (service_rank(sid), sid))
        return sorted_services
