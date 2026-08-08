"""SQLAlchemy ServiceHealth, HealthCheckRecord, and HealthEvent ORM models."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class HealthStatus(str, enum.Enum):
    """Standardized health states."""
    UNKNOWN = "UNKNOWN"
    STARTING = "STARTING"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    FAILED = "FAILED"


class ServiceHealthModel(Base):
    __tablename__ = "service_health"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deployment_services.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus, name="healthstatus"),
        nullable=False,
        default=HealthStatus.UNKNOWN,
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    consecutive_successes: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship
    deployment_service: Mapped["DeploymentServiceModel"] = relationship("DeploymentServiceModel")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ServiceHealthModel service_id={self.deployment_service_id} status={self.status}>"


class HealthCheckRecordModel(Base):
    __tablename__ = "health_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deployment_services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus, name="healthcheckstatus"),
        nullable=False,
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<HealthCheckRecordModel type={self.check_type} status={self.status} latency={self.latency_ms}ms>"


class HealthEventModel(Base):
    __tablename__ = "health_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_state: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<HealthEventModel type={self.event_type} service={self.service_id} new_state={self.new_state}>"
