"""SQLAlchemy ContainerMetrics and ObservabilityEvent ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base


class ContainerMetricsModel(Base):
    __tablename__ = "container_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    container_id: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    cpu_percent: Mapped[float] = mapped_column(Float(), nullable=False, default=0.0)
    memory_usage_bytes: Mapped[int] = mapped_column(BigInteger(), nullable=False, default=0)
    memory_limit_bytes: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    memory_percent: Mapped[float] = mapped_column(Float(), nullable=False, default=0.0)
    network_rx_bytes: Mapped[int] = mapped_column(BigInteger(), nullable=False, default=0)
    network_tx_bytes: Mapped[int] = mapped_column(BigInteger(), nullable=False, default=0)
    network_rx_rate: Mapped[float] = mapped_column(Float(), nullable=False, default=0.0)
    network_tx_rate: Mapped[float] = mapped_column(Float(), nullable=False, default=0.0)
    block_read_bytes: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    block_write_bytes: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    restart_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    container_state: Mapped[str] = mapped_column(String(50), nullable=False, default="running")

    def __repr__(self) -> str:
        return f"<ContainerMetricsModel service={self.service_id} cpu={self.cpu_percent}% memory={self.memory_percent}%>"


class ObservabilityEventModel(Base):
    __tablename__ = "observability_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ObservabilityEventModel type={self.event_type} service={self.service_id}>"
