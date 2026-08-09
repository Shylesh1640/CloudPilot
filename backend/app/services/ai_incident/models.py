from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class AIAnalysisStatus(StrEnum):
    AI_AVAILABLE = "AI_AVAILABLE"
    AI_UNAVAILABLE = "AI_UNAVAILABLE"
    AI_TIMEOUT = "AI_TIMEOUT"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"


class Confidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class IncidentRecommendation:
    action: str
    target: str
    reason: str
    confidence: Confidence


@dataclass(frozen=True)
class IncidentAnalysis:
    summary: str
    root_cause_service: str | None
    root_cause_type: str
    confidence: Confidence
    evidence: list[str]
    impact: list[str]
    recommendations: list[IncidentRecommendation]
    risk: str
    status: AIAnalysisStatus
    fallback: bool = False
