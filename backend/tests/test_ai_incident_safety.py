from app.services.ai_incident.evidence import redact
from app.services.ai_incident.models import Confidence, IncidentRecommendation
from app.services.ai_incident.recommendation import validate_recommendations


def test_redacts_common_secret_patterns() -> None:
    value = "Bearer abc.def.ghi password=hunter2 raw=eyJheader.payload.signature"
    redacted = redact(value)
    assert "abc.def.ghi" not in redacted
    assert "hunter2" not in redacted
    assert "eyJheader.payload.signature" not in redacted


def test_rejects_recommendation_outside_incident_context() -> None:
    recommendation = IncidentRecommendation("RESTART_SERVICE", "unknown-service", "test", Confidence.LOW)
    accepted, rejected = validate_recommendations(
        [recommendation], {"service": {"id": "api"}, "services": [{"id": "api"}]}
    )
    assert accepted == []
    assert rejected
