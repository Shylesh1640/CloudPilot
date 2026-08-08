"""Health Event Generator for recording state transition events."""
from __future__ import annotations

import uuid
from app.models.health import HealthStatus
from app.repositories.health_repository import HealthRepository


class HealthEventManager:
    def __init__(self, repo: HealthRepository) -> None:
        self.repo = repo

    async def emit_state_transition(
        self,
        project_id: uuid.UUID,
        deployment_id: uuid.UUID,
        service_id: str,
        previous_state: HealthStatus | str | None,
        new_state: HealthStatus | str,
        message: str | None = None,
    ) -> None:
        prev_str = str(previous_state.value if isinstance(previous_state, HealthStatus) else previous_state) if previous_state else None
        new_str = str(new_state.value if isinstance(new_state, HealthStatus) else new_state)

        if prev_str == new_str:
            return

        # Determine event_type string
        if new_str == "HEALTHY" and prev_str in ("UNHEALTHY", "DEGRADED", "FAILED"):
            event_type = "SERVICE_RECOVERED"
        else:
            event_type = f"SERVICE_{new_str}"

        evt_msg = message or f"Service '{service_id}' health state changed from {prev_str or 'NONE'} to {new_str}."

        await self.repo.record_event(
            project_id=project_id,
            deployment_id=deployment_id,
            service_id=service_id,
            event_type=event_type,
            previous_state=prev_str,
            new_state=new_str,
            message=evt_msg,
        )

    async def emit_flapping_event(
        self,
        project_id: uuid.UUID,
        deployment_id: uuid.UUID,
        service_id: str,
    ) -> None:
        await self.repo.record_event(
            project_id=project_id,
            deployment_id=deployment_id,
            service_id=service_id,
            event_type="HEALTH_FLAPPING",
            previous_state=None,
            new_state="DEGRADED",
            message=f"Service '{service_id}' is rapidly oscillating between HEALTHY and UNHEALTHY (flapping detected).",
        )
