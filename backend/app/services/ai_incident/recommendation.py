from __future__ import annotations

from app.services.ai_incident.models import Confidence, IncidentRecommendation

ALLOWED_RECOMMENDATIONS = {"RESTART_CONTAINER", "REPLACE_REPLICA", "RESTART_SERVICE", "RECONCILE_SERVICE", "SCALE_SERVICE", "ESCALATE"}


def validate_recommendations(recommendations: list[IncidentRecommendation], context: dict) -> tuple[list[IncidentRecommendation], list[str]]:
    services = {entry["id"] for entry in context.get("services", [])} | {context["service"]["id"]}
    accepted, rejected = [], []
    for item in recommendations:
        if item.action not in ALLOWED_RECOMMENDATIONS:
            rejected.append(f"Unsupported recovery action: {item.action}")
        elif item.target not in services:
            rejected.append(f"Recommendation target is not in the deployment: {item.target}")
        else:
            accepted.append(item)
    return accepted, rejected
