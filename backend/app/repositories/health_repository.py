"""Database access layer for health state, check history, and events."""
from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health import (
    HealthCheckRecordModel,
    HealthEventModel,
    HealthStatus,
    ServiceHealthModel,
)


class HealthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create_service_health(self, deployment_service_id: uuid.UUID) -> ServiceHealthModel:
        result = await self._session.execute(
            select(ServiceHealthModel).where(ServiceHealthModel.deployment_service_id == deployment_service_id)
        )
        health = result.scalar_one_or_none()
        if not health:
            health = ServiceHealthModel(
                deployment_service_id=deployment_service_id,
                status=HealthStatus.UNKNOWN,
                consecutive_failures=0,
                consecutive_successes=0,
            )
            self._session.add(health)
            await self._session.commit()
            await self._session.refresh(health)
        return health

    async def update_service_health(
        self,
        deployment_service_id: uuid.UUID,
        *,
        status: HealthStatus,
        consecutive_failures: int,
        consecutive_successes: int,
        latency_ms: int | None = None,
        last_error: str | None = None,
    ) -> ServiceHealthModel:
        health = await self.get_or_create_service_health(deployment_service_id)
        health.status = status
        health.consecutive_failures = consecutive_failures
        health.consecutive_successes = consecutive_successes
        health.latency_ms = latency_ms
        health.last_error = last_error
        now = datetime.datetime.now(datetime.timezone.utc)
        health.last_check_at = now

        if status == HealthStatus.HEALTHY:
            health.last_success_at = now
        elif status in (HealthStatus.UNHEALTHY, HealthStatus.FAILED, HealthStatus.DEGRADED):
            health.last_failure_at = now

        await self._session.commit()
        await self._session.refresh(health)
        return health

    async def add_check_record(
        self,
        *,
        deployment_service_id: uuid.UUID,
        check_type: str,
        status: HealthStatus,
        latency_ms: int | None = None,
        status_code: int | None = None,
        error_message: str | None = None,
        retention_limit: int = 100,
    ) -> HealthCheckRecordModel:
        record = HealthCheckRecordModel(
            deployment_service_id=deployment_service_id,
            check_type=check_type,
            status=status,
            latency_ms=latency_ms,
            status_code=status_code,
            error_message=error_message,
        )
        self._session.add(record)
        await self._session.commit()

        # Enforce retention cap (keep latest N entries per service)
        subq = (
            select(HealthCheckRecordModel.id)
            .where(HealthCheckRecordModel.deployment_service_id == deployment_service_id)
            .order_by(HealthCheckRecordModel.checked_at.desc())
            .offset(retention_limit)
        )
        old_ids_res = await self._session.execute(subq)
        old_ids = [r[0] for r in old_ids_res.all()]
        if old_ids:
            await self._session.execute(
                delete(HealthCheckRecordModel).where(HealthCheckRecordModel.id.in_(old_ids))
            )
            await self._session.commit()

        return record

    async def record_event(
        self,
        *,
        project_id: uuid.UUID,
        deployment_id: uuid.UUID,
        service_id: str,
        event_type: str,
        previous_state: str | None,
        new_state: str,
        message: str,
    ) -> HealthEventModel:
        evt = HealthEventModel(
            project_id=project_id,
            deployment_id=deployment_id,
            service_id=service_id,
            event_type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            message=message,
        )
        self._session.add(evt)
        await self._session.commit()
        await self._session.refresh(evt)
        return evt

    async def get_check_history(
        self,
        deployment_service_id: uuid.UUID,
        limit: int = 100,
    ) -> list[HealthCheckRecordModel]:
        result = await self._session.execute(
            select(HealthCheckRecordModel)
            .where(HealthCheckRecordModel.deployment_service_id == deployment_service_id)
            .order_by(HealthCheckRecordModel.checked_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_deployment_events(
        self,
        deployment_id: uuid.UUID,
        limit: int = 50,
    ) -> list[HealthEventModel]:
        result = await self._session.execute(
            select(HealthEventModel)
            .where(HealthEventModel.deployment_id == deployment_id)
            .order_by(HealthEventModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
