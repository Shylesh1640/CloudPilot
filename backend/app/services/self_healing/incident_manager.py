from __future__ import annotations

from app.models.self_healing import IncidentModel
from app.repositories.self_healing_repository import SelfHealingRepository


class IncidentManager:
    def __init__(self, repository: SelfHealingRepository) -> None:
        self.repository = repository

    async def open_or_update(self, deployment, service_id: str, trigger: str, severity: str, diagnosis: dict | None = None) -> tuple[IncidentModel, bool]:
        existing = await self.repository.active_incident(deployment.id, service_id, trigger)
        if existing:
            if diagnosis:
                existing.diagnosis = diagnosis
                await self.repository.save(existing)
            await self.repository.event(existing.id, "INCIDENT_UPDATED", "Repeated failure signal was correlated with the existing incident.")
            return existing, False
        incident = await self.repository.save(IncidentModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=service_id, severity=severity, status="OPEN", trigger=trigger, diagnosis=diagnosis))
        await self.repository.event(incident.id, "INCIDENT_CREATED", f"Incident opened for {service_id}: {trigger}.")
        return incident, True
