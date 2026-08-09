from __future__ import annotations

import time

from app.core.config import settings
from app.models.ai_incident import AIDecisionTraceModel, IncidentMemoryModel
from app.repositories.ai_incident_repository import AIIncidentRepository
from app.services.ai_incident.context_builder import IncidentContextBuilder
from app.services.ai_incident.fallback import deterministic_fallback
from app.services.ai_incident.models import AIAnalysisStatus, IncidentAnalysis
from app.services.ai_incident.prompt_builder import build_prompt
from app.services.ai_incident.provider import ConfiguredIncidentProvider, IncidentAIProvider
from app.services.ai_incident.recommendation import validate_recommendations
from app.services.ai_incident.structured_output import parse_output


class IncidentAnalyst:
    def __init__(self, session, provider: IncidentAIProvider | None = None) -> None:
        self.session = session
        self.repository = AIIncidentRepository(session)
        self.provider = provider or ConfiguredIncidentProvider()

    async def analyze(self, incident, force: bool = False) -> tuple[IncidentAnalysis, dict]:
        context, context_hash = await IncidentContextBuilder(self.session).build(incident)
        cached = await self.repository.cached_trace(incident.id, context_hash)
        if cached and cached.structured_result and not force:
            return self._from_saved(cached.structured_result), {"cached": True, "trace_id": str(cached.id), "validation": cached.validation_result}
        started = time.perf_counter()
        status, raw, error = await self.provider.analyze_incident(build_prompt(context))
        if raw is None:
            analysis = deterministic_fallback(context, status)
            validation = {"accepted": [item.action for item in analysis.recommendations], "rejected": [], "fallback": True}
        else:
            try:
                analysis = parse_output(raw, status)
                accepted, rejected = validate_recommendations(analysis.recommendations, context)
                analysis = IncidentAnalysis(analysis.summary, analysis.root_cause_service, analysis.root_cause_type, analysis.confidence, analysis.evidence, analysis.impact, accepted, analysis.risk, status)
                validation = {"accepted": [item.action for item in accepted], "rejected": rejected, "fallback": False}
            except Exception as exc:
                status, error = AIAnalysisStatus.AI_INVALID_RESPONSE, str(exc)
                analysis = deterministic_fallback(context, status)
                validation = {"accepted": [item.action for item in analysis.recommendations], "rejected": [error], "fallback": True}
        result = self._as_dict(analysis)
        trace = await self.repository.save(AIDecisionTraceModel(incident_id=incident.id, provider=settings.AI_PROVIDER, model=settings.AI_MODEL, context_hash=context_hash, status=status, structured_result=result, validation_result=validation, latency_ms=int((time.perf_counter() - started) * 1000), error_message=error))
        # Memory stores already-redacted structured evidence only; raw prompts/logs are never retained.
        if incident.status == "RESOLVED":
            memories = await self.repository.similar_memories(incident.project_id, incident.service_id, incident.trigger, 20)
            if not any(memory.incident_id == incident.id for memory in memories):
                await self.repository.save(IncidentMemoryModel(incident_id=incident.id, project_id=incident.project_id, service_id=incident.service_id, incident_type=incident.trigger, root_cause=analysis.root_cause_service, symptoms={"risk": analysis.risk}, evidence=analysis.evidence, successful_action=analysis.recommendations[0].action if analysis.recommendations else None))
        return analysis, {"cached": False, "trace_id": str(trace.id), "validation": validation}

    @staticmethod
    def _as_dict(value: IncidentAnalysis) -> dict:
        return {"summary": value.summary, "root_cause": {"service": value.root_cause_service, "type": value.root_cause_type, "confidence": value.confidence}, "evidence": value.evidence, "impact": value.impact, "recommendations": [{"action": item.action, "target": item.target, "reason": item.reason, "confidence": item.confidence} for item in value.recommendations], "risk": value.risk, "status": value.status, "fallback": value.fallback}

    @staticmethod
    def _from_saved(value: dict) -> IncidentAnalysis:
        return parse_output(value, AIAnalysisStatus(value.get("status", "AI_UNAVAILABLE")))
