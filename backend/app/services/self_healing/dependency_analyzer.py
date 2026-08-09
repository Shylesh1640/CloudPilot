from __future__ import annotations


class DependencyAnalyzer:
    """Uses the Phase 3 graph to isolate a root service and its dependants."""
    @staticmethod
    def impacted_services(plan_data: dict, root_service_id: str) -> list[str]:
        reverse: dict[str, list[str]] = {}
        for edge in plan_data.get("dependencies", []):
            if edge.get("required", True):
                reverse.setdefault(edge.get("target"), []).append(edge.get("source"))
        impacted, pending = [], list(reverse.get(root_service_id, []))
        while pending:
            service = pending.pop(0)
            if service in impacted:
                continue
            impacted.append(service)
            pending.extend(reverse.get(service, []))
        return impacted

    @staticmethod
    def unhealthy_dependency(plan_data: dict, service_id: str, health: dict[str, str]) -> str | None:
        for edge in plan_data.get("dependencies", []):
            if edge.get("source") == service_id and edge.get("required", True) and health.get(edge.get("target")) in {"UNHEALTHY", "FAILED"}:
                return str(edge["target"])
        return None
