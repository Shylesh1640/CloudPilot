"""Pydantic schemas for repository analysis API."""
from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, HttpUrl, field_validator

from app.models.repository_analysis import AnalysisStatus


# ── Request ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    repository_url: str

    @field_validator("repository_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not v.startswith("https://github.com/"):
            raise ValueError("Only public GitHub URLs are supported (https://github.com/owner/repo)")
        parts = v.removeprefix("https://github.com/").split("/")
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise ValueError("Invalid GitHub URL — must be https://github.com/owner/repository")
        return v


# ── Read responses ────────────────────────────────────────────────────────────

class AnalysisRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    repository_url: str
    repository_owner: str | None
    repository_name: str | None
    commit_sha: str | None
    status: AnalysisStatus
    progress: int
    primary_language: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResultRead(AnalysisRead):
    """Extends AnalysisRead to include the full normalized profile."""
    analysis_result: dict[str, Any] | None
