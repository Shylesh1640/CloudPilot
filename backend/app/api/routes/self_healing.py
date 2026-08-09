"""Authenticated, bounded Phase 8 reliability controls."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.database import AsyncSessionLocal
from app.models.self_healing import RecoveryPolicyModel
from app.models.user import User
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.self_healing_repository import SelfHealingRepository
from app.services.orchestrator import DockerRuntime
from app.services.self_healing.injection.controller import FailureInjectionController
from app.services.self_healing.schemas import FailureInjectionCreate, FailureInjectionRead, IncidentRead, RecoverRequest, RecoveryAttemptRead, RecoveryEventRead, RecoveryPolicyRead, RecoveryPolicyUpdate
from app.services.self_healing.worker import RecoveryWorker

router = APIRouter(prefix="/api/v1", tags=["Failure Injection & Self-Healing"])
recovery_worker: RecoveryWorker | None = None


def set_recovery_worker(worker: RecoveryWorker) -> None:
    global recovery_worker
    recovery_worker = worker


async def _deployment(session: AsyncSession, deployment_id: uuid.UUID, user_id: uuid.UUID):
    deployment = await DeploymentRepository(session).get(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found.")
    if not await ProjectRepository(session).get_by_id_for_user(deployment.project_id, user_id):
        raise HTTPException(status_code=403, detail="You are not authorized to operate this deployment.")
    return deployment


async def _incident(session: AsyncSession, incident_id: uuid.UUID, user_id: uuid.UUID):
    item = await SelfHealingRepository(session).incident(incident_id)
    if not item:
        raise HTTPException(status_code=404, detail="Incident not found.")
    await _deployment(session, item.deployment_id, user_id)
    return item


async def _run_injection(injection_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        await FailureInjectionController(session, DockerRuntime()).execute(injection_id)


@router.post("/deployments/{deployment_id}/failure-injections", response_model=FailureInjectionRead, status_code=status.HTTP_202_ACCEPTED)
async def inject_failure(deployment_id: uuid.UUID, payload: FailureInjectionCreate, tasks: BackgroundTasks, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deployment = await _deployment(session, deployment_id, current_user.id)
    candidates = [record for record in deployment.services if record.service_id == payload.service_id]
    service = next((record for record in candidates if payload.replica_id is None or record.replica_id == payload.replica_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Managed service or replica not found.")
    try:
        injection = await FailureInjectionController(session, DockerRuntime()).create(deployment, current_user.id, service, payload.scenario, payload.duration_seconds, payload.simulation)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    tasks.add_task(_run_injection, injection.id)
    return injection


@router.get("/deployments/{deployment_id}/incidents", response_model=list[IncidentRead])
async def list_incidents(deployment_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    await _deployment(session, deployment_id, current_user.id)
    return await SelfHealingRepository(session).incidents(deployment_id)


@router.get("/incidents/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await _incident(session, incident_id, current_user.id)


@router.get("/incidents/{incident_id}/timeline", response_model=list[RecoveryEventRead])
async def incident_timeline(incident_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    await _incident(session, incident_id, current_user.id)
    return await SelfHealingRepository(session).events(incident_id)


@router.get("/incidents/{incident_id}/recovery", response_model=list[RecoveryAttemptRead])
async def incident_recovery(incident_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    await _incident(session, incident_id, current_user.id)
    return await SelfHealingRepository(session).attempts(incident_id)


@router.post("/incidents/{incident_id}/recover", status_code=status.HTTP_202_ACCEPTED)
async def recover_incident(incident_id: uuid.UUID, payload: RecoverRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    incident = await _incident(session, incident_id, current_user.id)
    if not recovery_worker:
        raise HTTPException(status_code=503, detail="Recovery worker is unavailable.")
    incident.diagnosis = {**(incident.diagnosis or {}), "manual_action": payload.action, "dry_run": payload.dry_run}
    incident.status = "OPEN"
    repo = SelfHealingRepository(session)
    await repo.save(incident)
    await repo.audit(user_id=current_user.id, project_id=incident.project_id, deployment_id=incident.deployment_id, service_id=incident.service_id, action="MANUAL_RECOVERY", reason=payload.action, result="QUEUED", metadata={"dry_run": payload.dry_run})
    await recovery_worker.enqueue(incident.id)
    return {"incident_id": str(incident.id), "status": "QUEUED"}


@router.get("/deployments/{deployment_id}/services/{service_id}/recovery-policy", response_model=RecoveryPolicyRead)
async def get_recovery_policy(deployment_id: uuid.UUID, service_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deployment = await _deployment(session, deployment_id, current_user.id)
    if not any(record.service_id == service_id for record in deployment.services):
        raise HTTPException(status_code=404, detail="Service not found.")
    repo = SelfHealingRepository(session)
    policy = await repo.policy(deployment_id, service_id)
    if not policy:
        policy = await repo.save(RecoveryPolicyModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=service_id))
    return policy


@router.put("/deployments/{deployment_id}/services/{service_id}/recovery-policy", response_model=RecoveryPolicyRead)
async def update_recovery_policy(deployment_id: uuid.UUID, service_id: str, payload: RecoveryPolicyUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deployment = await _deployment(session, deployment_id, current_user.id)
    repo = SelfHealingRepository(session)
    policy = await repo.policy(deployment_id, service_id) or RecoveryPolicyModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=service_id)
    for key, value in payload.model_dump().items():
        setattr(policy, key, value)
    return await repo.save(policy)
