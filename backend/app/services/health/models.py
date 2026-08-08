"""Internal Pydantic models for Health Check execution."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field
from app.models.health import HealthStatus


class HealthCheckResult(BaseModel):
    service_id: str
    check_type: Literal["HTTP", "TCP", "CONTAINER"]
    status: HealthStatus
    latency_ms: int | None = None
    status_code: int | None = None
    error_message: str | None = None
    timestamp: str | None = None
