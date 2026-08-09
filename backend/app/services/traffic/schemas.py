from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class TrafficRunCreate(BaseModel):
    service_id: str = Field(min_length=1, max_length=100)
    scenario: Literal["constant", "ramp_up", "ramp_down", "spike"]
    requests_per_second: float | None = Field(default=None, gt=0)
    start_rps: float | None = Field(default=None, gt=0)
    end_rps: float | None = Field(default=None, gt=0)
    baseline_rps: float | None = Field(default=None, gt=0)
    spike_rps: float | None = Field(default=None, gt=0)
    spike_duration_seconds: int | None = Field(default=None, ge=1)
    duration_seconds: int = Field(ge=1)
    path: str = Field(default="/", max_length=200, pattern=r"^/[A-Za-z0-9_./-]*$")

    @model_validator(mode="after")
    def scenario_fields(self):
        if self.scenario == "constant" and self.requests_per_second is None:
            raise ValueError("requests_per_second is required for constant traffic")
        if self.scenario in {"ramp_up", "ramp_down"} and (self.start_rps is None or self.end_rps is None):
            raise ValueError("start_rps and end_rps are required for ramp traffic")
        if self.scenario == "spike" and (self.baseline_rps is None or self.spike_rps is None or self.spike_duration_seconds is None):
            raise ValueError("baseline_rps, spike_rps and spike_duration_seconds are required for spike traffic")
        return self


class TrafficRunRead(BaseModel):
    id: UUID
    project_id: UUID
    deployment_id: UUID
    service_id: str
    scenario: str
    configuration: dict
    status: str
    current_rps: float
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
