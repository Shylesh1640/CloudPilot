"""Observability policy defaults and threshold parameters."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ObservabilityPolicy(BaseModel):
    metrics_interval_seconds: int = Field(default=5, ge=1, le=60)
    telemetry_retention_hours: int = Field(default=24, ge=1, le=168)
    high_cpu_threshold_percent: float = Field(default=80.0, ge=10.0, le=100.0)
    high_memory_threshold_percent: float = Field(default=90.0, ge=10.0, le=100.0)


DEFAULT_OBSERVABILITY_POLICY = ObservabilityPolicy()
