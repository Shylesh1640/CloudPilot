"""SQLAlchemy InfrastructurePlan model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PlanStatus(str, enum.Enum):
    """Lifecycle states for an infrastructure plan."""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InfrastructurePlanModel(Base):
    __tablename__ = "infrastructure_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repository_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repository_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="planstatus"),
        nullable=False,
        default=PlanStatus.PENDING,
    )
    plan_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    validation_result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    ai_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_duration_ms: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship("Project")  # noqa: F821
    analysis: Mapped["RepositoryAnalysis"] = relationship("RepositoryAnalysis")  # noqa: F821

    def __repr__(self) -> str:
        return f"<InfrastructurePlanModel id={self.id} version={self.version} status={self.status}>"
