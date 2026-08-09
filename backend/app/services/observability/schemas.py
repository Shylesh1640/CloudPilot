"""API response schemas for metrics and WebSocket telemetry."""
from __future__ import annotations

import datetime
from typing import Any
import uuid

from pydantic import BaseModel


class ContainerMetricsRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    deployment_id: uuid.UUID
    service_id: str
    container_id: str
    timestamp: datetime.datetime
    cpu_percent: float
    memory_usage_bytes: int
    memory_limit_bytes: int | None
    memory_percent: float
    network_rx_bytes: int
    network_tx_bytes: int
    network_rx_rate: float
    network_tx_rate: float
    block_read_bytes: int | None
    block_write_bytes: int | None
    restart_count: int
    container_state: str

    model_config = {"from_attributes": True}


class ServiceMetricsRead(BaseModel):
    service_id: str
    timestamp: datetime.datetime
    cpu_percent: float
    memory_usage_bytes: int
    memory_limit_bytes: int | None
    memory_percent: float
    network_rx_rate: float
    network_tx_rate: float
    restart_count: int
    container_state: str

    model_config = {"from_attributes": True}


class DeploymentMetricsRead(BaseModel):
    deployment_id: uuid.UUID
    timestamp: datetime.datetime
    total_cpu_percent: float
    avg_cpu_percent: float
    total_memory_usage_bytes: int
    avg_memory_percent: float
    total_network_rx_rate: float
    total_network_tx_rate: float
    total_restarts: int
    services: dict[str, ServiceMetricsRead]


class LogEntry(BaseModel):
    timestamp: str
    level: str = "INFO"
    message: str


class LogEntriesRead(BaseModel):
    service_id: str
    lines: list[LogEntry]
    logs: list[str] = []
