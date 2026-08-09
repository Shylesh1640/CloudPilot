from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ScalingPolicyUpdate(BaseModel):
    enabled: bool = True
    min_replicas: int = Field(default=1, ge=1)
    max_replicas: int = Field(default=3, ge=1)
    target_cpu: float | None = Field(default=70, gt=0, le=100)
    target_memory: float | None = Field(default=None, gt=0, le=100)
    target_request_rate: float | None = Field(default=None, gt=0)
    target_latency: float | None = Field(default=None, gt=0)
    scale_up_threshold: float | None = Field(default=None, gt=0)
    scale_down_threshold: float | None = Field(default=None, ge=0)
    scale_up_cooldown: int = Field(default=60, ge=0, le=3600)
    scale_down_cooldown: int = Field(default=120, ge=0, le=3600)
    stabilization_window: int = Field(default=60, ge=1, le=3600)
    max_scale_up_step: int = Field(default=2, ge=1, le=100)
    max_scale_down_step: int = Field(default=1, ge=1, le=100)
    dry_run: bool = False
    simulation_mode: bool = False

    @model_validator(mode="after")
    def valid_range(self):
        if self.min_replicas > self.max_replicas:
            raise ValueError("min_replicas must not exceed max_replicas")
        if self.scale_up_threshold is not None and self.scale_down_threshold is not None and self.scale_down_threshold >= self.scale_up_threshold:
            raise ValueError("scale_down_threshold must be lower than scale_up_threshold to preserve hysteresis")
        return self


class ScalingPolicyRead(ScalingPolicyUpdate):
    id: UUID
    project_id: UUID
    deployment_id: UUID
    service_id: str
    last_scale_up_at: datetime | None = None
    last_scale_down_at: datetime | None = None
    cooldown_remaining_seconds: int = 0
    model_config = {"from_attributes": True}


class ToggleAutoscalingRequest(BaseModel):
    enabled: bool


class ManualScaleRequest(BaseModel):
    replicas: int = Field(ge=1, le=100)
    dry_run: bool = False


class SimulationEvaluationRequest(BaseModel):
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    memory_percent: float | None = Field(default=None, ge=0, le=100)
    request_rate: float | None = Field(default=None, ge=0)
    p95_latency: float | None = Field(default=None, ge=0)


class ScalingDecisionRead(BaseModel):
    id: UUID
    service_id: str
    current_replicas: int
    recommended_replicas: int
    action: str
    status: str
    trigger_metric: str | None
    metric_value: float | None
    target_value: float | None
    reason: str
    metrics_json: dict | None
    created_at: datetime
    model_config = {"from_attributes": True}


class ScalingEventRead(BaseModel):
    id: UUID
    service_id: str
    event_type: str
    message: str
    metadata_json: dict | None
    created_at: datetime
    model_config = {"from_attributes": True}
