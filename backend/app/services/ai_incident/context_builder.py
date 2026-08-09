"""Builds a small, redacted, incident-scoped context; never an entire DB dump."""
from __future__ import annotations

import hashlib
import json

from app.core.config import settings
from app.models.infrastructure_plan import InfrastructurePlanModel
from app.repositories.ai_incident_repository import AIIncidentRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.health_repository import HealthRepository
from app.repositories.observability_repository import ObservabilityRepository
from app.repositories.self_healing_repository import SelfHealingRepository
from app.services.ai_incident.evidence import redact_structure
from app.services.observability.log_manager import LogManager


class IncidentContextBuilder:
    def __init__(self, session) -> None:
        self.session = session

    async def build(self, incident) -> tuple[dict, str]:
        deployment = await DeploymentRepository(self.session).get(incident.deployment_id)
        plan = await self.session.get(InfrastructurePlanModel, deployment.infrastructure_plan_id)
        plan_data = plan.plan_data if plan and plan.plan_data else {"dependencies": []}
        health_repo, metrics_repo, recovery_repo = HealthRepository(self.session), ObservabilityRepository(self.session), SelfHealingRepository(self.session)
        services, health, metrics = [], {}, {}
        for record in deployment.services:
            current = await health_repo.get_or_create_service_health(record.id)
            health[record.service_id] = current.status.value
            if record.service_id == incident.service_id or record.service_id == incident.root_cause_service_id:
                latest = await metrics_repo.get_latest_for_service(deployment.id, record.service_id)
                if latest:
                    metrics[record.service_id] = {"cpu_percent": latest.cpu_percent, "memory_percent": latest.memory_percent, "container_state": latest.container_state}
                services.append({"id": record.service_id, "container_state": record.actual_state.value, "replica_id": record.replica_id, "desired_replicas": record.desired_replicas})
        dependencies = [edge for edge in plan_data.get("dependencies", []) if edge.get("source") == incident.service_id or edge.get("target") == incident.service_id]
        target = next((record for record in deployment.services if record.service_id == incident.service_id), None)
        logs = []
        if target:
            try:
                limit = settings.AI_INCIDENT_CONTEXT_LOG_LINES
                logs = LogManager().get_container_logs(incident.service_id, target.container_name, tail=limit).logs[-limit:]
            except Exception:
                logs = []
        event_limit = settings.AI_INCIDENT_CONTEXT_EVENTS
        history_limit = settings.AI_INCIDENT_HISTORY_LIMIT
        events = [{"type": event.event_type, "message": event.message} for event in (await recovery_repo.events(incident.id))[-event_limit:]]
        memories = await AIIncidentRepository(self.session).similar_memories(incident.project_id, incident.service_id, incident.trigger, history_limit)
        context = {"incident": {"id": str(incident.id), "severity": incident.severity, "status": incident.status, "trigger": incident.trigger}, "service": {"id": incident.service_id, "health": health.get(incident.service_id, "UNKNOWN")}, "root_cause_candidate": incident.root_cause_service_id, "services": services, "health": health, "metrics": metrics, "dependencies": dependencies, "logs": logs, "events": events, "historical": [{"incident_type": memory.incident_type, "root_cause": memory.root_cause, "successful_action": memory.successful_action, "evidence": memory.evidence} for memory in memories]}
        context = redact_structure(context)
        encoded = json.dumps(context, sort_keys=True, separators=(",", ":"))
        return context, hashlib.sha256(encoded.encode()).hexdigest()
