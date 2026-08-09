from __future__ import annotations

from app.services.ai_incident.models import AIAnalysisStatus, Confidence, IncidentAnalysis, IncidentRecommendation
from app.services.ai_incident.schemas import IncidentAIOutput


def parse_output(value: dict, status: AIAnalysisStatus) -> IncidentAnalysis:
    result = IncidentAIOutput.model_validate(value)
    root = result.root_cause if isinstance(result.root_cause, dict) else {}
    recommendations = [IncidentRecommendation(item.action, item.target, item.reason, Confidence(item.confidence)) for item in result.recommendations]
    return IncidentAnalysis(summary=result.summary, root_cause_service=root.get("service"), root_cause_type=str(root.get("type", "UNKNOWN")), confidence=Confidence(str(root.get("confidence", "UNCERTAIN"))), evidence=result.evidence, impact=result.impact, recommendations=recommendations, risk=result.risk, status=status)
