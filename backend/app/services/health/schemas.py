"""Pydantic API response schemas for Health endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel
from app.models.health import HealthStatus


class ServiceHealthRead(BaseModel):
    id: uuid.UUID
    deployment_service_id: uuid.UUID
    service_id: str
    status: HealthStatus
    consecutive_failures: int
    consecutive_successes: int
    latency_ms: int | None
    last_check_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class HealthCheckRecordRead(BaseModel):
    id: uuid.UUID
    deployment_service_id: uuid.UUID
    check_type: str
    status: HealthStatus
    latency_ms: int | None
    status_code: int | None
    error_message: str | None
    checked_at: datetime

    model_config = {"from_attributes": True}


class HealthEventRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    deployment_id: uuid.UUID
    service_id: str
    event_type: str
    previous_state: str | None
    new_state: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DeploymentHealthRead(BaseModel):
    deployment_id: uuid.UUID
    status: HealthStatus
    overall_health: HealthStatus
    services: dict[str, HealthStatus]
    avg_latency_ms: int | None = None
