"""Pydantic schemas for infrastructure plan API responses."""
from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel

from app.models.infrastructure_plan import PlanStatus


class PlanRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    repository_analysis_id: uuid.UUID
    version: int
    status: PlanStatus
    ai_provider: str | None
    ai_model: str | None
    generation_duration_ms: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanResultRead(PlanRead):
    """Extends PlanRead to include full validated plan_data and validation_result."""
    plan_data: dict[str, Any] | None
    validation_result: dict[str, Any] | None
