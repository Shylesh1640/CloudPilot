"""SQLAlchemy RepositoryAnalysis model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AnalysisStatus(str, enum.Enum):
    """Lifecycle states for a repository analysis run."""
    PENDING = "PENDING"
    CLONING = "CLONING"
    SCANNING = "SCANNING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RepositoryAnalysis(Base):
    __tablename__ = "repository_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repository_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    repository_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    repository_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysisstatus"),
        nullable=False,
        default=AnalysisStatus.PENDING,
    )
    progress: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    primary_language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    analysis_result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship("Project")  # noqa: F821

    def __repr__(self) -> str:
        return f"<RepositoryAnalysis id={self.id} status={self.status}>"
