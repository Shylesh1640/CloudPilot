"""API endpoints for Deployment & Health Check Engine."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.health.schemas import (
    DeploymentHealthRead,
    HealthCheckRecordRead,
    HealthEventRead,
    ServiceHealthRead,
)
from app.services.health_service import HealthService

router = APIRouter(prefix="", tags=["Health Engine"])


@router.get(
    "/deployments/{deployment_id}/health",
    response_model=DeploymentHealthRead,
    summary="Get overall deployment health",
)
async def get_deployment_health(
    deployment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeploymentHealthRead:
    svc = HealthService(db)
    return await svc.get_deployment_health(deployment_id, current_user.id)


@router.get(
    "/deployments/{deployment_id}/services/{service_id}/health",
    response_model=ServiceHealthRead,
    summary="Get specific service health state",
)
async def get_service_health(
    deployment_id: uuid.UUID,
    service_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceHealthRead:
    svc = HealthService(db)
    return await svc.get_service_health(deployment_id, service_id, current_user.id)


@router.get(
    "/deployments/{deployment_id}/services/{service_id}/health/history",
    response_model=list[HealthCheckRecordRead],
    summary="Get service health check history",
)
async def get_service_health_history(
    deployment_id: uuid.UUID,
    service_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[HealthCheckRecordRead]:
    svc = HealthService(db)
    return await svc.get_service_health_history(deployment_id, service_id, current_user.id, limit=limit)


@router.get(
    "/deployments/{deployment_id}/health/events",
    response_model=list[HealthEventRead],
    summary="Get deployment health transition events",
)
async def get_deployment_health_events(
    deployment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[HealthEventRead]:
    svc = HealthService(db)
    return await svc.get_deployment_events(deployment_id, current_user.id, limit=limit)
