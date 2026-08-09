"""Adapts Phase 6 telemetry without fabricating app-level metrics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.observability_repository import ObservabilityRepository
from app.services.autoscaling.models import MetricSnapshot


class MetricsAdapter:
    def __init__(self, repository: ObservabilityRepository) -> None:
        self.repository = repository

    async def recent_snapshot(self, deployment_id, service_id: str, window_seconds: int) -> MetricSnapshot | None:
        start = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        samples = await self.repository.get_service_history(deployment_id, service_id, start_time=start, limit=500)
        if not samples:
            return None
        latest = samples[-1]
        return MetricSnapshot(timestamp=latest.timestamp, cpu_percent=sum(s.cpu_percent for s in samples) / len(samples), memory_percent=sum(s.memory_percent for s in samples) / len(samples))
