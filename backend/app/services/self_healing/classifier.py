from __future__ import annotations

from app.services.self_healing.dependency_analyzer import DependencyAnalyzer
from app.services.self_healing.models import Diagnosis


class FailureClassifier:
    @staticmethod
    def diagnose(service_id: str, container_state: str, health: dict[str, str], plan_data: dict) -> Diagnosis:
        dependency = DependencyAnalyzer.unhealthy_dependency(plan_data, service_id, health)
        if dependency:
            return Diagnosis(service_id, "DEPENDENCY_FAILED", dependency, DependencyAnalyzer.impacted_services(plan_data, dependency), [f"{dependency} health = {health.get(dependency)}", f"{service_id} depends on {dependency}"])
        if container_state.lower() in {"exited", "dead"}:
            return Diagnosis(service_id, "CONTAINER_EXITED", service_id, DependencyAnalyzer.impacted_services(plan_data, service_id), [f"container state = {container_state}", f"{service_id} health = {health.get(service_id, 'UNKNOWN')}"])
        return Diagnosis(service_id, "SERVICE_UNHEALTHY", service_id, DependencyAnalyzer.impacted_services(plan_data, service_id), [f"{service_id} health = {health.get(service_id, 'UNKNOWN')}"])
