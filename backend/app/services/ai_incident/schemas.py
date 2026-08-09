from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RecommendationOutput(BaseModel):
    action: Literal["RESTART_CONTAINER", "REPLACE_REPLICA", "RESTART_SERVICE", "RECONCILE_SERVICE", "SCALE_SERVICE", "ESCALATE"]
    target: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)
    confidence: Literal["HIGH", "MEDIUM", "LOW", "UNCERTAIN"]


class IncidentAIOutput(BaseModel):
    summary: str = Field(min_length=1, max_length=3000)
    root_cause: dict
    evidence: list[str] = Field(default_factory=list, max_length=20)
    impact: list[str] = Field(default_factory=list, max_length=20)
    recommendations: list[RecommendationOutput] = Field(default_factory=list, max_length=5)
    risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"] = "UNKNOWN"


class IncidentQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class IncidentAnalysisRead(BaseModel):
    summary: str
    root_cause: dict
    evidence: list[str]
    impact: list[str]
    recommendations: list[dict]
    risk: str
    status: str
    fallback: bool = False
    cached: bool = False
    trace_id: str
    validation: dict
