from __future__ import annotations

from app.services.ai_incident.models import AIAnalysisStatus, Confidence, IncidentAnalysis, IncidentRecommendation


def deterministic_fallback(context: dict, status: AIAnalysisStatus) -> IncidentAnalysis:
    incident, root = context["incident"], context.get("root_cause_candidate") or context["service"]["id"]
    evidence = [event["message"] for event in context.get("events", [])[-3:]] or [f"{context['service']['id']} health = {context['service']['health']}"]
    action = "RESTART_SERVICE" if incident["trigger"] in {"SERVICE_UNHEALTHY", "DEPENDENCY_FAILED"} else "RESTART_CONTAINER"
    return IncidentAnalysis(summary=f"Deterministic fallback: {context['service']['id']} has an active {incident['trigger']} incident. Root candidate is {root}.", root_cause_service=root, root_cause_type=incident["trigger"], confidence=Confidence.LOW, evidence=evidence, impact=[], recommendations=[IncidentRecommendation(action, root, "Fallback uses the existing deterministic recovery policy; provider output is unavailable.", Confidence.LOW)], risk="UNKNOWN", status=status, fallback=True)
