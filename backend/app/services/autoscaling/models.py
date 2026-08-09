"""Pure deterministic autoscaling domain objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID


class ScalingAction(StrEnum):
    NO_ACTION = "NO_ACTION"
    SCALE_UP = "SCALE_UP"
    SCALE_DOWN = "SCALE_DOWN"
    BLOCKED = "BLOCKED"


class DecisionStatus(StrEnum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class MetricSnapshot:
    timestamp: datetime
    cpu_percent: float | None = None
    memory_percent: float | None = None
    request_rate: float | None = None
    p95_latency: float | None = None

    def as_dict(self) -> dict[str, float | None]:
        return {"cpu_percent": self.cpu_percent, "memory_percent": self.memory_percent, "request_rate": self.request_rate, "p95_latency": self.p95_latency}


@dataclass(frozen=True)
class Policy:
    min_replicas: int = 1
    max_replicas: int = 3
    target_cpu: float | None = 70.0
    target_memory: float | None = None
    target_request_rate: float | None = None
    target_latency: float | None = None
    scale_up_threshold: float | None = None
    scale_down_threshold: float | None = None
    max_scale_up_step: int = 2
    max_scale_down_step: int = 1

    def validate(self) -> None:
        if self.min_replicas < 1 or self.max_replicas < self.min_replicas:
            raise ValueError("Replica limits must be positive and min_replicas must not exceed max_replicas.")
        if self.max_scale_up_step < 1 or self.max_scale_down_step < 1:
            raise ValueError("Scale step limits must be at least one.")


@dataclass
class ScalingDecision:
    service_id: str
    current_replicas: int
    recommended_replicas: int
    action: ScalingAction
    reason: str
    metrics: dict[str, float | None] = field(default_factory=dict)
    trigger_metric: str | None = None
    metric_value: float | None = None
    target_value: float | None = None
    status: DecisionStatus = DecisionStatus.PENDING
    confidence: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    record_id: UUID | None = None
