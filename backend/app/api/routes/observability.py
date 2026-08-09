"""API REST and WebSocket endpoints for Real-Time Observability Platform."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import AsyncSessionLocal, get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.services.observability.schemas import (
    ContainerMetricsRead,
    DeploymentMetricsRead,
    LogEntriesRead,
    ServiceMetricsRead,
)
from app.services.observability.websocket_manager import ws_manager
from app.services.observability_service import ObservabilityService

router = APIRouter(prefix="", tags=["Observability Platform"])


@router.get(
    "/deployments/{deployment_id}/metrics",
    response_model=DeploymentMetricsRead,
    summary="Get deployment-wide metrics telemetry",
)
async def get_deployment_metrics(
    deployment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeploymentMetricsRead:
    svc = ObservabilityService(db)
    return await svc.get_deployment_metrics(deployment_id, current_user.id)


@router.get(
    "/deployments/{deployment_id}/services/{service_id}/metrics/current",
    response_model=ServiceMetricsRead,
    summary="Get current service metrics snapshot",
)
async def get_service_current_metrics(
    deployment_id: uuid.UUID,
    service_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceMetricsRead:
    svc = ObservabilityService(db)
    return await svc.get_service_current_metrics(deployment_id, service_id, current_user.id)


@router.get(
    "/deployments/{deployment_id}/services/{service_id}/metrics",
    response_model=list[ContainerMetricsRead],
    summary="Get service time-series metrics history",
)
async def get_service_metrics_history(
    deployment_id: uuid.UUID,
    service_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    minutes: Annotated[int, Query(ge=1, le=1440)] = 15,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[ContainerMetricsRead]:
    svc = ObservabilityService(db)
    return await svc.get_service_metrics_history(
        deployment_id=deployment_id,
        service_id=service_id,
        user_id=current_user.id,
        minutes=minutes,
        limit=limit,
    )


@router.get(
    "/deployments/{deployment_id}/services/{service_id}/logs",
    response_model=LogEntriesRead,
    summary="Get service container stdout/stderr logs with level search",
)
async def get_container_logs(
    deployment_id: uuid.UUID,
    service_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    tail: Annotated[int, Query(ge=1, le=1000)] = 100,
    level: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> LogEntriesRead:
    svc = ObservabilityService(db)
    return await svc.get_container_logs(
        deployment_id=deployment_id,
        service_id=service_id,
        user_id=current_user.id,
        tail=tail,
        level_filter=level,
        search_term=search,
    )


@router.websocket("/ws/deployments/{deployment_id}")
async def websocket_telemetry_endpoint(
    websocket: WebSocket,
    deployment_id: uuid.UUID,
    token: str = Query(...),
) -> None:
    """WebSocket endpoint for real-time telemetry streaming."""
    # Authenticate token
    try:
        payload = decode_access_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if not payload or not payload.get("sub"):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = uuid.UUID(payload["sub"])
    str_dep_id = str(deployment_id)

    # Verify project authorization
    async with AsyncSessionLocal() as session:
        dep_repo = DeploymentRepository(session)
        proj_repo = ProjectRepository(session)
        deployment = await dep_repo.get(deployment_id)
        if not deployment:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        project = await proj_repo.get_by_id_for_user(deployment.project_id, user_id)
        if not project:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws_manager.connect(str_dep_id, websocket)
    try:
        while True:
            # Keep socket open and receive any client ping messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        await ws_manager.disconnect(str_dep_id, websocket)
    except Exception:
        await ws_manager.disconnect(str_dep_id, websocket)
