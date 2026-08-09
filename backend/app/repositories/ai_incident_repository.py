from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.ai_incident import AIDecisionTraceModel, IncidentMemoryModel


class AIIncidentRepository:
    def __init__(self, session) -> None:
        self.session = session

    async def save(self, item):
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def cached_trace(self, incident_id: uuid.UUID, context_hash: str) -> AIDecisionTraceModel | None:
        return (await self.session.execute(select(AIDecisionTraceModel).where(AIDecisionTraceModel.incident_id == incident_id, AIDecisionTraceModel.context_hash == context_hash, AIDecisionTraceModel.status.in_(("AI_AVAILABLE", "AI_UNAVAILABLE"))).order_by(AIDecisionTraceModel.created_at.desc()).limit(1))).scalar_one_or_none()

    async def similar_memories(self, project_id: uuid.UUID, service_id: str, incident_type: str, limit: int = 5) -> list[IncidentMemoryModel]:
        result = await self.session.execute(select(IncidentMemoryModel).where(IncidentMemoryModel.project_id == project_id, IncidentMemoryModel.service_id == service_id, IncidentMemoryModel.incident_type == incident_type).order_by(IncidentMemoryModel.created_at.desc()).limit(limit))
        return list(result.scalars())
