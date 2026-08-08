"""Deployment & Service Orchestration API routes."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.deployment_service import ActiveDeploymentConflictError, DeploymentService, run_background_deployment
from app.services.orchestrator.schemas import DeploymentRead, DeploymentServiceRead, ServiceLogsRead

router = APIRouter(prefix="/api/v1", tags=["Container Orchestration"])


@router.post(
    "/infrastructure-plans/{plan_id}/deploy",
    response_model=DeploymentRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute Infrastructure Plan Container Deployment",
    description="Transforms a validated infrastructure plan into running Docker containers.",
)
async def trigger_deployment(
    plan_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DeploymentRead:
    service = DeploymentService(session)
    try:
        deployment = await service.trigger_deployment(
            plan_id=plan_id,
            user_id=current_user.id,
        )
    except ActiveDeploymentConflictError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    # Schedule background worker task
    background_tasks.add_task(run_background_deployment, deployment.id)

    return DeploymentRead.model_validate(deployment)


@router.get(
    "/deployments/{deployment_id}",
    response_model=DeploymentRead,
    summary="Get deployment status and timeline progress",
)
async def get_deployment_status(
    deployment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DeploymentRead:
    service = DeploymentService(session)
    deployment = await service.get_deployment(deployment_id, current_user.id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment record not found or access denied",
        )
    return DeploymentRead.model_validate(deployment)


@router.get(
    "/deployments/{deployment_id}/services",
    response_model=list[DeploymentServiceRead],
    summary="Get deployment services with desired vs actual runtime states",
)
async def get_deployment_services(
    deployment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[DeploymentServiceRead]:
    service = DeploymentService(session)
    deployment = await service.get_deployment(deployment_id, current_user.id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment record not found or access denied",
        )
    return [DeploymentServiceRead.model_validate(s) for s in deployment.services]


@router.post(
    "/deployments/{deployment_id}/stop",
    response_model=DeploymentRead,
    summary="Stop all deployment containers",
)
async def stop_deployment(
    deployment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DeploymentRead:
    service = DeploymentService(session)
    try:
        deployment = await service.stop_deployment(deployment_id, current_user.id)
        return DeploymentRead.model_validate(deployment)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post(
    "/deployments/{deployment_id}/services/{service_id}/restart",
    status_code=status.HTTP_200_OK,
    summary="Restart a specific deployment service container",
)
async def restart_service(
    deployment_id: uuid.UUID,
    service_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = DeploymentService(session)
    try:
        await service.restart_service(deployment_id, service_id, current_user.id)
        return {"success": True, "message": f"Service '{service_id}' restarted successfully."}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get(
    "/deployments/{deployment_id}/services/{service_id}/logs",
    response_model=ServiceLogsRead,
    summary="Get recent logs for a specific service container",
)
async def get_service_logs(
    deployment_id: uuid.UUID,
    service_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ServiceLogsRead:
    service = DeploymentService(session)
    try:
        logs_text = await service.get_service_logs(deployment_id, service_id, current_user.id, limit=limit)
        return ServiceLogsRead(
            service_id=service_id,
            container_name=f"cloudpilot-{service_id}",
            logs=logs_text,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
