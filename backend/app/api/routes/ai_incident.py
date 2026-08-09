"""Phase 9 advisory incident intelligence; this router never executes recovery."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.self_healing_repository import SelfHealingRepository
from app.services.ai_incident.analyst import IncidentAnalyst
from app.services.ai_incident.schemas import IncidentAnalysisRead, IncidentQuestion
from app.api.routes.self_healing import _incident

router = APIRouter(prefix="/api/v1", tags=["AI Incident Intelligence"])


def _analysis_payload(analysis, metadata: dict) -> dict:
    return {"summary": analysis.summary, "root_cause": {"service": analysis.root_cause_service, "type": analysis.root_cause_type, "confidence": analysis.confidence}, "evidence": analysis.evidence, "impact": analysis.impact, "recommendations": [{"action": item.action, "target": item.target, "reason": item.reason, "confidence": item.confidence} for item in analysis.recommendations], "risk": analysis.risk, "status": analysis.status, "fallback": analysis.fallback, **metadata}


@router.get("/incidents/{incident_id}/ai-analysis", response_model=IncidentAnalysisRead)
async def get_ai_analysis(incident_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    incident = await _incident(session, incident_id, current_user.id)
    analysis, metadata = await IncidentAnalyst(session).analyze(incident)
    return _analysis_payload(analysis, metadata)


@router.post("/incidents/{incident_id}/ai-analysis", response_model=IncidentAnalysisRead)
async def refresh_ai_analysis(incident_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    incident = await _incident(session, incident_id, current_user.id)
    analysis, metadata = await IncidentAnalyst(session).analyze(incident, force=True)
    await SelfHealingRepository(session).audit(user_id=current_user.id, project_id=incident.project_id, deployment_id=incident.deployment_id, service_id=incident.service_id, action="AI_ANALYSIS_REQUESTED", reason="Manual incident analysis", result=analysis.status)
    return _analysis_payload(analysis, metadata)


@router.post("/incidents/{incident_id}/assistant")
async def incident_assistant(incident_id: uuid.UUID, payload: IncidentQuestion, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """A context-bounded helper, deliberately not a general-purpose command interface."""
    question = payload.question.lower()
    if any(term in question for term in ("docker", "shell", "command", "delete", "exec", "bash", "shutdown")):
        return {"answer": "Infrastructure changes must go through CloudPilot's controlled recovery policy and safety validator; this assistant cannot execute or provide commands."}
    incident = await _incident(session, incident_id, current_user.id)
    analysis, _ = await IncidentAnalyst(session).analyze(incident)
    if "evidence" in question or "why" in question:
        answer = analysis.summary + " Evidence: " + "; ".join(analysis.evidence[:5])
    elif "action" in question or "recover" in question:
        recommendation = analysis.recommendations[0] if analysis.recommendations else None
        answer = f"Recommended action: {recommendation.action} for {recommendation.target}. {recommendation.reason}" if recommendation else "No safe recommendation is available; the incident should be escalated."
    elif "affected" in question or "impact" in question:
        answer = "Affected services: " + (", ".join(analysis.impact) if analysis.impact else "unknown from current evidence")
    else:
        answer = analysis.summary
    return {"answer": answer, "status": analysis.status, "fallback": analysis.fallback}
