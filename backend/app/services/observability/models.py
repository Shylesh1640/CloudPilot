"""Internal Pydantic models for raw and normalized container telemetry."""
from __future__ import annotations

import datetime
from pydantic import BaseModel, Field


class NormalizedContainerMetrics(BaseModel):
    project_id: str
    deployment_id: str
    service_id: str
    container_id: str
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    cpu_percent: float = 0.0
    memory_usage_bytes: int = 0
    memory_limit_bytes: int | None = None
    memory_percent: float = 0.0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    network_rx_rate: float = 0.0
    network_tx_rate: float = 0.0
    block_read_bytes: int | None = None
    block_write_bytes: int | None = None
    restart_count: int = 0
    container_state: str = "running"
