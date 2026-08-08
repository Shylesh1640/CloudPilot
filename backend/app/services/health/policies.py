"""Default policies and configurable threshold parameters for Health Engine."""
from __future__ import annotations

from pydantic import BaseModel, Field


class HealthPolicy(BaseModel):
    failure_threshold: int = Field(default=3, ge=1, le=10)
    success_threshold: int = Field(default=2, ge=1, le=10)
    startup_grace_period_seconds: int = Field(default=30, ge=0, le=300)
    deployment_timeout_seconds: int = Field(default=120, ge=10, le=600)
    check_interval_seconds: int = Field(default=10, ge=1, le=60)
    history_retention_limit: int = Field(default=100, ge=10, le=1000)
    flapping_window_seconds: int = Field(default=300, ge=60, le=1800)
    flapping_threshold_switches: int = Field(default=4, ge=2, le=20)


DEFAULT_HEALTH_POLICY = HealthPolicy()
