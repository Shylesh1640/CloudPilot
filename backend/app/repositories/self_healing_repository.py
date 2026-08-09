"""Single persistence boundary for Phase 8's durable audit trail."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.self_healing import AuditLogModel, FailureInjectionModel, IncidentModel, RecoveryAttemptModel, RecoveryEventModel, RecoveryPolicyModel

ACTIVE_INCIDENTS = ("OPEN", "INVESTIGATING", "RECOVERING", "VERIFYING")


class SelfHealingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, item):
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def policy(self, deployment_id: uuid.UUID, service_id: str) -> RecoveryPolicyModel | None:
        return (await self.session.execute(select(RecoveryPolicyModel).where(RecoveryPolicyModel.deployment_id == deployment_id, RecoveryPolicyModel.service_id == service_id))).scalar_one_or_none()

    async def incident(self, incident_id: uuid.UUID) -> IncidentModel | None:
        return await self.session.get(IncidentModel, incident_id)

    async def active_incident(self, deployment_id: uuid.UUID, service_id: str, trigger: str) -> IncidentModel | None:
        return (await self.session.execute(select(IncidentModel).where(IncidentModel.deployment_id == deployment_id, IncidentModel.service_id == service_id, IncidentModel.trigger == trigger, IncidentModel.status.in_(ACTIVE_INCIDENTS)))).scalar_one_or_none()

    async def incidents(self, deployment_id: uuid.UUID, limit: int = 100) -> list[IncidentModel]:
        return list((await self.session.execute(select(IncidentModel).where(IncidentModel.deployment_id == deployment_id).order_by(IncidentModel.opened_at.desc()).limit(limit))).scalars())

    async def attempts(self, incident_id: uuid.UUID) -> list[RecoveryAttemptModel]:
        return list((await self.session.execute(select(RecoveryAttemptModel).where(RecoveryAttemptModel.incident_id == incident_id).order_by(RecoveryAttemptModel.attempt_number))).scalars())

    async def events(self, incident_id: uuid.UUID) -> list[RecoveryEventModel]:
        return list((await self.session.execute(select(RecoveryEventModel).where(RecoveryEventModel.incident_id == incident_id).order_by(RecoveryEventModel.created_at))).scalars())

    async def event(self, incident_id: uuid.UUID, kind: str, message: str, metadata: dict | None = None) -> RecoveryEventModel:
        return await self.save(RecoveryEventModel(incident_id=incident_id, event_type=kind, message=message, metadata_json=metadata))

    async def audit(self, *, user_id: uuid.UUID | None, project_id: uuid.UUID, deployment_id: uuid.UUID, service_id: str | None, action: str, reason: str | None, result: str, metadata: dict | None = None) -> AuditLogModel:
        return await self.save(AuditLogModel(user_id=user_id, project_id=project_id, deployment_id=deployment_id, service_id=service_id, action=action, reason=reason, result=result, metadata_json=metadata))

    async def injection(self, injection_id: uuid.UUID) -> FailureInjectionModel | None:
        return await self.session.get(FailureInjectionModel, injection_id)

    async def active_injections(self, deployment_id: uuid.UUID) -> int:
        return len(list((await self.session.execute(select(FailureInjectionModel.id).where(FailureInjectionModel.deployment_id == deployment_id, FailureInjectionModel.status.in_(("PENDING", "RUNNING"))))).scalars()))

    async def update_incident(self, incident: IncidentModel, status: str, *, resolved: bool = False) -> IncidentModel:
        incident.status = status
        if resolved:
            incident.resolved_at = datetime.now(timezone.utc)
        return await self.save(incident)
