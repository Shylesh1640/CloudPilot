"""Database access layer for deployments and deployment services."""
from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deployment import (
    DeploymentModel,
    DeploymentServiceModel,
    DeploymentStatus,
    ServiceActualState,
    ServiceDesiredState,
)


class DeploymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        project_id: uuid.UUID,
        infrastructure_plan_id: uuid.UUID,
        version: int = 1,
    ) -> DeploymentModel:
        deployment = DeploymentModel(
            project_id=project_id,
            infrastructure_plan_id=infrastructure_plan_id,
            version=version,
            status=DeploymentStatus.PENDING,
            progress=0,
            logs=[],
            services=[],
        )
        self._session.add(deployment)
        await self._session.commit()
        await self._session.refresh(deployment)
        return deployment

    async def get(self, deployment_id: uuid.UUID) -> DeploymentModel | None:
        result = await self._session.execute(
            select(DeploymentModel)
            .where(DeploymentModel.id == deployment_id)
            .options(selectinload(DeploymentModel.services))
        )
        return result.scalar_one_or_none()

    async def get_active_for_project(self, project_id: uuid.UUID) -> DeploymentModel | None:
        """Find any deployment for this project that is currently in progress."""
        active_statuses = [
            DeploymentStatus.PENDING,
            DeploymentStatus.PREPARING,
            DeploymentStatus.BUILDING,
            DeploymentStatus.CREATING_NETWORK,
            DeploymentStatus.CREATING_VOLUMES,
            DeploymentStatus.CREATING_SERVICES,
            DeploymentStatus.STARTING,
        ]
        result = await self._session.execute(
            select(DeploymentModel)
            .where(DeploymentModel.project_id == project_id)
            .where(DeploymentModel.status.in_(active_statuses))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_project(self, project_id: uuid.UUID) -> DeploymentModel | None:
        result = await self._session.execute(
            select(DeploymentModel)
            .where(DeploymentModel.project_id == project_id)
            .options(selectinload(DeploymentModel.services))
            .order_by(DeploymentModel.version.desc(), DeploymentModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        deployment_id: uuid.UUID,
        *,
        status: DeploymentStatus,
        progress: int | None = None,
        error_message: str | None = None,
        log_entry: str | None = None,
    ) -> None:
        deployment = await self.get(deployment_id)
        if not deployment:
            return

        deployment.status = status
        if progress is not None:
            deployment.progress = progress
        if error_message:
            deployment.error_message = error_message

        if status == DeploymentStatus.RUNNING and not deployment.started_at:
            deployment.started_at = datetime.datetime.now(datetime.timezone.utc)
        elif status in (DeploymentStatus.FAILED, DeploymentStatus.STOPPED):
            deployment.completed_at = datetime.datetime.now(datetime.timezone.utc)

        if log_entry:
            current_logs = list(deployment.logs or [])
            current_logs.append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "message": log_entry,
            })
            deployment.logs = current_logs

        await self._session.commit()

    async def add_service(
        self,
        *,
        deployment_id: uuid.UUID,
        service_id: str,
        container_name: str,
        image: str,
        port: int | None = None,
        public: bool = False,
    ) -> DeploymentServiceModel:
        svc = DeploymentServiceModel(
            deployment_id=deployment_id,
            service_id=service_id,
            container_name=container_name,
            image=image,
            port=port,
            public=public,
            desired_state=ServiceDesiredState.RUNNING,
            actual_state=ServiceActualState.CREATED,
            status="CREATED",
        )
        self._session.add(svc)
        await self._session.commit()
        await self._session.refresh(svc)
        return svc

    async def update_service_state(
        self,
        service_record_id: uuid.UUID,
        *,
        container_id: str | None = None,
        desired_state: ServiceDesiredState | None = None,
        actual_state: ServiceActualState | None = None,
        status: str | None = None,
        error_message: str | None = None,
    ) -> None:
        result = await self._session.execute(
            select(DeploymentServiceModel).where(DeploymentServiceModel.id == service_record_id)
        )
        svc = result.scalar_one_or_none()
        if not svc:
            return

        if container_id:
            svc.container_id = container_id
        if desired_state:
            svc.desired_state = desired_state
        if actual_state:
            svc.actual_state = actual_state
            if actual_state == ServiceActualState.RUNNING and not svc.started_at:
                svc.started_at = datetime.datetime.now(datetime.timezone.utc)
            elif actual_state == ServiceActualState.EXITED:
                svc.stopped_at = datetime.datetime.now(datetime.timezone.utc)
        if status:
            svc.status = status
        if error_message:
            svc.error_message = error_message

        await self._session.commit()
