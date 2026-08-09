"""Database access layer for time-series container metrics and telemetry events."""
from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import ContainerMetricsModel, ObservabilityEventModel


class ObservabilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_metrics(self, metrics: ContainerMetricsModel) -> ContainerMetricsModel:
        self._session.add(metrics)
        await self._session.commit()
        await self._session.refresh(metrics)
        return metrics

    async def add_metrics_batch(self, batch: list[ContainerMetricsModel]) -> None:
        if not batch:
            return
        self._session.add_all(batch)
        await self._session.commit()

    async def get_latest_for_service(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
    ) -> ContainerMetricsModel | None:
        result = await self._session.execute(
            select(ContainerMetricsModel)
            .where(ContainerMetricsModel.deployment_id == deployment_id)
            .where(ContainerMetricsModel.service_id == service_id)
            .order_by(ContainerMetricsModel.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_service_history(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
        start_time: datetime.datetime | None = None,
        end_time: datetime.datetime | None = None,
        limit: int = 200,
    ) -> list[ContainerMetricsModel]:
        query = (
            select(ContainerMetricsModel)
            .where(ContainerMetricsModel.deployment_id == deployment_id)
            .where(ContainerMetricsModel.service_id == service_id)
        )

        if start_time:
            query = query.where(ContainerMetricsModel.timestamp >= start_time)
        if end_time:
            query = query.where(ContainerMetricsModel.timestamp <= end_time)

        query = query.order_by(ContainerMetricsModel.timestamp.asc()).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_deployment_history(
        self,
        deployment_id: uuid.UUID,
        start_time: datetime.datetime | None = None,
        limit: int = 500,
    ) -> list[ContainerMetricsModel]:
        query = select(ContainerMetricsModel).where(ContainerMetricsModel.deployment_id == deployment_id)
        if start_time:
            query = query.where(ContainerMetricsModel.timestamp >= start_time)
        query = query.order_by(ContainerMetricsModel.timestamp.asc()).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def purge_old_metrics(self, retention_hours: int = 24) -> int:
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=retention_hours)
        stmt = delete(ContainerMetricsModel).where(ContainerMetricsModel.timestamp <= cutoff)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount or 0

    async def add_event(
        self,
        project_id: uuid.UUID,
        deployment_id: uuid.UUID,
        service_id: str,
        event_type: str,
        message: str,
        severity: str = "info",
        metadata_json: dict[str, Any] | None = None,
    ) -> ObservabilityEventModel:
        evt = ObservabilityEventModel(
            project_id=project_id,
            deployment_id=deployment_id,
            service_id=service_id,
            event_type=event_type,
            severity=severity,
            message=message,
            metadata_json=metadata_json,
        )
        self._session.add(evt)
        await self._session.commit()
        await self._session.refresh(evt)
        return evt
