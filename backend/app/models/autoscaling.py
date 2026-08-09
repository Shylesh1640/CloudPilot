"""Persistent Phase 7 traffic and deterministic autoscaling state."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScalingPolicyModel(Base):
    __tablename__ = "scaling_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    min_replicas: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    max_replicas: Mapped[int] = mapped_column(Integer(), nullable=False, default=3)
    target_cpu: Mapped[float | None] = mapped_column(Float(), nullable=True, default=70.0)
    target_memory: Mapped[float | None] = mapped_column(Float(), nullable=True)
    target_request_rate: Mapped[float | None] = mapped_column(Float(), nullable=True)
    target_latency: Mapped[float | None] = mapped_column(Float(), nullable=True)
    scale_up_threshold: Mapped[float | None] = mapped_column(Float(), nullable=True)
    scale_down_threshold: Mapped[float | None] = mapped_column(Float(), nullable=True)
    scale_up_cooldown: Mapped[int] = mapped_column(Integer(), nullable=False, default=60)
    scale_down_cooldown: Mapped[int] = mapped_column(Integer(), nullable=False, default=120)
    stabilization_window: Mapped[int] = mapped_column(Integer(), nullable=False, default=60)
    max_scale_up_step: Mapped[int] = mapped_column(Integer(), nullable=False, default=2)
    max_scale_down_step: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    dry_run: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    simulation_mode: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    last_scale_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_scale_down_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ScalingDecisionModel(Base):
    __tablename__ = "scaling_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    current_replicas: Mapped[int] = mapped_column(Integer(), nullable=False)
    recommended_replicas: Mapped[int] = mapped_column(Integer(), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    trigger_metric: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metric_value: Mapped[float | None] = mapped_column(Float(), nullable=True)
    target_value: Mapped[float | None] = mapped_column(Float(), nullable=True)
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ScalingEventModel(Base):
    __tablename__ = "scaling_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TrafficRunModel(Base):
    __tablename__ = "traffic_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario: Mapped[str] = mapped_column(String(30), nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    current_rps: Mapped[float] = mapped_column(Float(), nullable=False, default=0.0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
