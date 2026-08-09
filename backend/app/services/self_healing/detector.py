from __future__ import annotations

from app.models.health import HealthStatus


class FailureDetector:
    @staticmethod
    def is_confirmed(health_record, container_state: str) -> str | None:
        if container_state.lower() in {"exited", "dead"}:
            return "CONTAINER_EXITED"
        if health_record.status in {HealthStatus.UNHEALTHY, HealthStatus.FAILED} and health_record.consecutive_failures > 0:
            return "SERVICE_UNHEALTHY"
        return None
