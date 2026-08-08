"""Configurable scan and analysis limits."""
from __future__ import annotations

from dataclasses import dataclass
from app.core.config import settings


@dataclass(frozen=True)
class AnalysisLimits:
    max_files: int = settings.MAX_REPO_FILES
    max_repo_size_mb: int = settings.MAX_REPO_SIZE_MB
    max_file_size_kb: int = settings.MAX_FILE_SIZE_KB
    clone_timeout_seconds: int = settings.GIT_CLONE_TIMEOUT_SECONDS
    analysis_timeout_seconds: int = settings.ANALYSIS_TIMEOUT_SECONDS


DEFAULT_LIMITS = AnalysisLimits()
