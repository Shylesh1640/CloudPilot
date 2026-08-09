"""SQLAlchemy Deployment and DeploymentService ORM models."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DeploymentStatus(str, enum.Enum):
    """Orchestration deployment statuses."""
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    BUILDING = "BUILDING"
    CREATING_NETWORK = "CREATING_NETWORK"
    CREATING_VOLUMES = "CREATING_VOLUMES"
    CREATING_SERVICES = "CREATING_SERVICES"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class ServiceDesiredState(str, enum.Enum):
    """Desired state requested by CloudPilot."""
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class ServiceActualState(str, enum.Enum):
    """Actual container runtime state observed from Docker Engine."""
    RUNNING = "RUNNING"
    STARTING = "STARTING"
    EXITED = "EXITED"
    CREATED = "CREATED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class DeploymentModel(Base):
    __tablename__ = "deployments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    infrastructure_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("infrastructure_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus, name="deploymentstatus"),
        nullable=False,
        default=DeploymentStatus.PENDING,
    )
    progress: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    logs: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, default=list
    )
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship("Project")  # noqa: F821
    plan: Mapped["InfrastructurePlanModel"] = relationship("InfrastructurePlanModel")  # noqa: F821
    services: Mapped[list["DeploymentServiceModel"]] = relationship(
        "DeploymentServiceModel", back_populates="deployment", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DeploymentModel id={self.id} version={self.version} status={self.status}>"


class DeploymentServiceModel(Base):
    __tablename__ = "deployment_services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[str] = mapped_column(String(100), nullable=False)
    container_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    container_name: Mapped[str] = mapped_column(String(200), nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    desired_state: Mapped[ServiceDesiredState] = mapped_column(
        Enum(ServiceDesiredState, name="servicedesiredstate"),
        nullable=False,
        default=ServiceDesiredState.RUNNING,
    )
    actual_state: Mapped[ServiceActualState] = mapped_column(
        Enum(ServiceActualState, name="serviceactualstate"),
        nullable=False,
        default=ServiceActualState.UNKNOWN,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    port: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    # Replica intent is owned by CloudPilot; actual replicas are reconciled from
    # the managed container records/runtime by the Phase 7 replica manager.
    desired_replicas: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    replica_id: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)

    # ── Relationship ─────────────────────────────────────────────────────────
    deployment: Mapped[DeploymentModel] = relationship("DeploymentModel", back_populates="services")

    def __repr__(self) -> str:
        return f"<DeploymentServiceModel service_id={self.service_id} desired={self.desired_state} actual={self.actual_state}>"
