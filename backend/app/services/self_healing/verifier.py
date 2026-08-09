from __future__ import annotations

import asyncio

from app.models.health import HealthStatus
from app.repositories.health_repository import HealthRepository


class RecoveryVerifier:
    def __init__(self, session, runtime) -> None:
        self.session = session
        self.runtime = runtime
        self.health = HealthRepository(session)

    async def verify_service(self, deployment, service_id: str) -> tuple[bool, str]:
        records = [record for record in deployment.services if record.service_id == service_id]
        if not records:
            return False, "No managed service records remain."
        for record in records:
            state = self.runtime.inspect_container(record.container_id or record.container_name).get("State", {})
            if not state.get("Running", False):
                return False, f"Container {record.container_name} is not running."
            health = await self.health.get_or_create_service_health(record.id)
            if health.status != HealthStatus.HEALTHY:
                return False, f"Container {record.container_name} has not passed Phase 5 health verification."
        return True, "All target replicas are running and healthy."

    async def wait_for_service(self, deployment, service_id: str, timeout_seconds: int) -> tuple[bool, str]:
        """Wait in the worker (never an HTTP handler) for Phase 5 verification."""
        for _ in range(max(1, timeout_seconds // 2)):
            verified, message = await self.verify_service(deployment, service_id)
            if verified:
                return verified, message
            await asyncio.sleep(2)
        return await self.verify_service(deployment, service_id)
