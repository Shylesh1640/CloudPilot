"""Authenticated Phase 7 autoscaling and controlled traffic endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.database import AsyncSessionLocal
from app.models.autoscaling import ScalingDecisionModel, ScalingPolicyModel
from app.models.infrastructure_plan import InfrastructurePlanModel
from app.models.user import User
from app.repositories.autoscaling_repository import AutoscalingRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.observability_repository import ObservabilityRepository
from app.repositories.project_repository import ProjectRepository
from app.services.autoscaling.cooldown import cooldown_remaining
from app.services.autoscaling.evaluator import AutoscalingEvaluator
from app.services.autoscaling.metrics_adapter import MetricsAdapter
from app.services.autoscaling.replica_manager import ReplicaManager
from app.services.autoscaling.safety import validate_scaling_target
from app.services.autoscaling.scaler import Autoscaler
from app.services.autoscaling.models import MetricSnapshot, ScalingAction
from app.services.autoscaling.schemas import ManualScaleRequest, ScalingDecisionRead, ScalingEventRead, ScalingPolicyRead, ScalingPolicyUpdate, SimulationEvaluationRequest, ToggleAutoscalingRequest
from app.services.orchestrator import DockerRuntime
from app.services.traffic.controller import TrafficController
from app.services.traffic.schemas import TrafficRunCreate, TrafficRunRead

router = APIRouter(prefix="/api/v1", tags=["Traffic & Autoscaling"])


async def _deployment_for_user(session: AsyncSession, deployment_id: uuid.UUID, user_id: uuid.UUID):
    deployment = await DeploymentRepository(session).get(deployment_id)
    if not deployment or not await ProjectRepository(session).get_by_id_for_user(deployment.project_id, user_id):
        raise HTTPException(status_code=404, detail="Deployment not found or access denied.")
    return deployment


async def _service_definition(session: AsyncSession, deployment, service_id: str) -> dict:
    plan = await session.get(InfrastructurePlanModel, deployment.infrastructure_plan_id)
    services = (plan.plan_data or {}).get("services", []) if plan else []
    definition = next((item for item in services if item.get("id") == service_id), None)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' is not part of this deployment plan.")
    return definition


async def _policy(session: AsyncSession, deployment, service_id: str, definition: dict) -> ScalingPolicyModel:
    repository = AutoscalingRepository(session)
    existing = await repository.get_policy(deployment.id, service_id)
    if existing:
        return existing
    replicas = definition.get("replicas") or {}
    policy = ScalingPolicyModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=service_id, min_replicas=int(replicas.get("min", 1)), max_replicas=int(replicas.get("max", 3)), target_cpu=70.0)
    return await repository.save_policy(policy)


def _policy_read(policy: ScalingPolicyModel) -> ScalingPolicyRead:
    remaining = max(cooldown_remaining(policy, "SCALE_UP"), cooldown_remaining(policy, "SCALE_DOWN"))
    return ScalingPolicyRead.model_validate(policy).model_copy(update={"cooldown_remaining_seconds": remaining})


@router.get("/deployments/{deployment_id}/services/{service_id}/scaling", response_model=ScalingPolicyRead)
async def get_scaling_policy(deployment_id: uuid.UUID, service_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deployment = await _deployment_for_user(session, deployment_id, current_user.id)
    definition = await _service_definition(session, deployment, service_id)
    if not definition.get("scalable", False):
        raise HTTPException(status_code=409, detail="SCALING_NOT_SUPPORTED: service is not scalable.")
    return _policy_read(await _policy(session, deployment, service_id, definition))


@router.put("/deployments/{deployment_id}/services/{service_id}/scaling", response_model=ScalingPolicyRead)
async def update_scaling_policy(deployment_id: uuid.UUID, service_id: str, payload: ScalingPolicyUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deployment = await _deployment_for_user(session, deployment_id, current_user.id)
    definition = await _service_definition(session, deployment, service_id)
    if not definition.get("scalable", False):
        raise HTTPException(status_code=409, detail="SCALING_NOT_SUPPORTED: service is not scalable.")
    policy = await _policy(session, deployment, service_id, definition)
    for key, value in payload.model_dump().items():
        setattr(policy, key, value)
    return _policy_read(await AutoscalingRepository(session).save_policy(policy))


@router.post("/deployments/{deployment_id}/services/{service_id}/scaling/toggle", response_model=ScalingPolicyRead)
async def toggle_autoscaling(deployment_id: uuid.UUID, service_id: str, payload: ToggleAutoscalingRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deployment = await _deployment_for_user(session, deployment_id, current_user.id)
    definition = await _service_definition(session, deployment, service_id)
    if not definition.get("scalable", False):
        raise HTTPException(status_code=409, detail="SCALING_NOT_SUPPORTED: service is not scalable.")
    policy = await _policy(session, deployment, service_id, definition)
    policy.enabled = payload.enabled
    return _policy_read(await AutoscalingRepository(session).save_policy(policy))


@router.post("/deployments/{deployment_id}/services/{service_id}/scale")
async def manual_scale(deployment_id: uuid.UUID, service_id: str, payload: ManualScaleRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deployment = await _deployment_for_user(session, deployment_id, current_user.id)
    definition = await _service_definition(session, deployment, service_id)
    policy = await _policy(session, deployment, service_id, definition)
    issue = validate_scaling_target(deployment, service_id, bool(definition.get("scalable")), payload.replicas, policy.min_replicas, policy.max_replicas)
    if issue:
        raise HTTPException(status_code=409, detail=issue)
    manager = ReplicaManager(session, DockerRuntime())
    current = await manager.get_current_replicas(deployment.id, service_id)
    if payload.dry_run:
        return {"action": "NO_ACTION" if current == payload.replicas else "MANUAL_SCALE", "current_replicas": current, "recommended_replicas": payload.replicas, "dry_run": True}
    actual = await manager.scale_to(deployment, service_id, payload.replicas)
    repository = AutoscalingRepository(session)
    action = ScalingAction.SCALE_UP if actual > current else ScalingAction.SCALE_DOWN if actual < current else ScalingAction.NO_ACTION
    await repository.record_decision(ScalingDecisionModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=service_id, current_replicas=current, recommended_replicas=actual, action=action, status="COMPLETED", reason="Manual scaling request."))
    await AutoscalingEvaluator(repository, MetricsAdapter(ObservabilityRepository(session))).event(deployment, service_id, "MANUAL_SCALE_COMPLETED", f"Manual scale set {service_id} to {actual} replicas.")
    return {"action": "NO_ACTION" if current == actual else "MANUAL_SCALE", "current_replicas": current, "recommended_replicas": actual, "dry_run": False}


@router.post("/deployments/{deployment_id}/services/{service_id}/scaling/evaluate")
async def evaluate_simulation(deployment_id: uuid.UUID, service_id: str, payload: SimulationEvaluationRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """Evaluate synthetic metrics only when the stored policy explicitly enables simulation."""
    deployment = await _deployment_for_user(session, deployment_id, current_user.id)
    definition = await _service_definition(session, deployment, service_id)
    policy = await _policy(session, deployment, service_id, definition)
    if not policy.simulation_mode:
        raise HTTPException(status_code=409, detail="Simulation mode is disabled for this policy.")
    issue = validate_scaling_target(deployment, service_id, bool(definition.get("scalable")), policy.min_replicas, policy.min_replicas, policy.max_replicas)
    if issue:
        raise HTTPException(status_code=409, detail=issue)
    repository = AutoscalingRepository(session)
    manager = ReplicaManager(session, DockerRuntime())
    current = await manager.get_current_replicas(deployment.id, service_id)
    evaluator = AutoscalingEvaluator(repository, MetricsAdapter(ObservabilityRepository(session)))
    decision = await evaluator.evaluate(deployment, service_id, current, policy, MetricSnapshot(timestamp=datetime.now(timezone.utc), **payload.model_dump()))
    decision = await Autoscaler(evaluator, manager).apply(deployment, policy, decision)
    return {"action": decision.action, "status": decision.status, "current_replicas": decision.current_replicas, "recommended_replicas": decision.recommended_replicas, "reason": decision.reason}


@router.get("/deployments/{deployment_id}/scaling/decisions", response_model=list[ScalingDecisionRead])
async def scaling_decisions(deployment_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    await _deployment_for_user(session, deployment_id, current_user.id)
    return await AutoscalingRepository(session).decisions(deployment_id)


@router.get("/deployments/{deployment_id}/scaling/events", response_model=list[ScalingEventRead])
async def scaling_events(deployment_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    await _deployment_for_user(session, deployment_id, current_user.id)
    return await AutoscalingRepository(session).events(deployment_id)


async def _run_traffic(run_id: uuid.UUID, target_url: str) -> None:
    async with AsyncSessionLocal() as session:
        await TrafficController(AutoscalingRepository(session)).execute(run_id, target_url)


@router.post("/deployments/{deployment_id}/traffic", response_model=TrafficRunRead, status_code=status.HTTP_202_ACCEPTED)
async def start_traffic(deployment_id: uuid.UUID, payload: TrafficRunCreate, tasks: BackgroundTasks, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deployment = await _deployment_for_user(session, deployment_id, current_user.id)
    definition = await _service_definition(session, deployment, payload.service_id)
    service = next((item for item in deployment.services if item.service_id == payload.service_id and item.public), None)
    if not service or not service.port or deployment.status.value != "RUNNING":
        raise HTTPException(status_code=409, detail="Traffic targets must be active, CloudPilot-managed public services.")
    run = await TrafficController(AutoscalingRepository(session)).create(deployment, current_user.id, payload)
    # The URL is derived only from the managed service record; callers cannot supply a target host.
    tasks.add_task(_run_traffic, run.id, f"http://{service.container_name}:{service.port}")
    return run


@router.post("/traffic/{traffic_run_id}/stop", response_model=TrafficRunRead)
async def stop_traffic(traffic_run_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    repository = AutoscalingRepository(session)
    run = await repository.get_traffic_run(traffic_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Traffic run not found.")
    await _deployment_for_user(session, run.deployment_id, current_user.id)
    return await TrafficController(repository).stop(run)


@router.get("/traffic/{traffic_run_id}", response_model=TrafficRunRead)
async def traffic_status(traffic_run_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    run = await AutoscalingRepository(session).get_traffic_run(traffic_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Traffic run not found.")
    await _deployment_for_user(session, run.deployment_id, current_user.id)
    return run


@router.get("/deployments/{deployment_id}/traffic", response_model=list[TrafficRunRead])
async def traffic_history(deployment_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    await _deployment_for_user(session, deployment_id, current_user.id)
    return await AutoscalingRepository(session).traffic_runs(deployment_id)
