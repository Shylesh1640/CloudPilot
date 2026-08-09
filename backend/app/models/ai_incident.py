"""Auditable, redacted Phase 9 incident intelligence records."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

Json = JSON().with_variant(JSONB, "postgresql")


class IncidentMemoryModel(Base):
    __tablename__ = "incident_memory"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), unique=True, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[str] = mapped_column(String(100), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False)
    root_cause: Mapped[str | None] = mapped_column(String(100))
    symptoms: Mapped[dict[str, Any]] = mapped_column(Json, nullable=False, default=dict)
    evidence: Mapped[list[str]] = mapped_column(Json, nullable=False, default=list)
    successful_action: Mapped[str | None] = mapped_column(String(50))
    recovery_time_seconds: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AIDecisionTraceModel(Base):
    __tablename__ = "ai_decision_traces"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    structured_result: Mapped[dict[str, Any] | None] = mapped_column(Json)
    validation_result: Mapped[dict[str, Any] | None] = mapped_column(Json)
    latency_ms: Mapped[int | None] = mapped_column()
    error_message: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
