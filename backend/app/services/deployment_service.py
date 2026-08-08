"""DeploymentService — High level coordinator for container deployments, control operations, and background workers."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.deployment import DeploymentModel, DeploymentStatus, ServiceDesiredState
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.project_repository import ProjectRepository
from app.services.ai.schemas import InfrastructurePlan
from app.services.orchestrator import DeploymentEngine, DockerRuntime, ServiceManager, OrchestratorError

logger = logging.getLogger("cloudpilot.deployment_service")


class ActiveDeploymentConflictError(Exception):
    """Raised when attempting to trigger deployment while one is already active for the project."""
    pass


class DeploymentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._deployment_repo = DeploymentRepository(session)
        self._plan_repo = PlanRepository(session)
        self._project_repo = ProjectRepository(session)
        self._analysis_repo = AnalysisRepository(session)

    async def trigger_deployment(
        self,
        *,
        plan_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DeploymentModel:
        """Verify plan existence & ownership, check active concurrency, and create deployment record."""
        plan_record = await self._plan_repo.get(plan_id)
        if not plan_record:
            raise ValueError("Infrastructure plan record not found.")

        project = await self._project_repo.get_by_id_for_user(plan_record.project_id, user_id)
        if not project:
            raise ValueError("Project not found or access denied.")

        if plan_record.status != "COMPLETED" or not plan_record.plan_data:
            raise ValueError("Infrastructure plan must be COMPLETED before executing deployment.")

        # Check concurrency (active deployment in progress)
        active = await self._deployment_repo.get_active_for_project(plan_record.project_id)
        if active:
            raise ActiveDeploymentConflictError("A deployment is already in progress for this project.")

        latest = await self._deployment_repo.get_latest_for_project(plan_record.project_id)
        next_version = (latest.version + 1) if latest else 1

        deployment = await self._deployment_repo.create(
            project_id=plan_record.project_id,
            infrastructure_plan_id=plan_id,
            version=next_version,
        )
        return deployment

    async def get_deployment(
        self,
        deployment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DeploymentModel | None:
        """Get deployment record verifying project ownership."""
        deployment = await self._deployment_repo.get(deployment_id)
        if not deployment:
            return None

        project = await self._project_repo.get_by_id_for_user(deployment.project_id, user_id)
        if not project:
            return None

        return deployment

    async def stop_deployment(
        self,
        deployment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DeploymentModel:
        """Stop all running containers for a deployment."""
        deployment = await self.get_deployment(deployment_id, user_id)
        if not deployment:
            raise ValueError("Deployment record not found or access denied.")

        service_mgr = ServiceManager(DockerRuntime())
        for svc in deployment.services:
            if svc.container_name:
                try:
                    service_mgr.stop_service(svc.container_name)
                    await self._deployment_repo.update_service_state(
                        svc.id,
                        desired_state=ServiceDesiredState.STOPPED,
                        status="STOPPED",
                    )
                except Exception as err:
                    logger.warning(f"Error stopping container {svc.container_name}: {err}")

        await self._deployment_repo.update_status(
            deployment_id,
            status=DeploymentStatus.STOPPED,
            log_entry="All deployment services stopped by user.",
        )
        await self._session.refresh(deployment)
        return deployment

    async def restart_service(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
        user_id: uuid.UUID,
    ) -> None:
        """Restart a specific service container."""
        deployment = await self.get_deployment(deployment_id, user_id)
        if not deployment:
            raise ValueError("Deployment record not found or access denied.")

        svc = next((s for s in deployment.services if s.service_id == service_id), None)
        if not svc or not svc.container_name:
            raise ValueError(f"Service '{service_id}' not found in deployment.")

        service_mgr = ServiceManager(DockerRuntime())
        service_mgr.restart_service(svc.container_name)
        await self._deployment_repo.update_service_state(
            svc.id,
            desired_state=ServiceDesiredState.RUNNING,
            status="RUNNING",
        )

    async def get_service_logs(
        self,
        deployment_id: uuid.UUID,
        service_id: str,
        user_id: uuid.UUID,
        limit: int = 200,
    ) -> str:
        """Fetch container logs for a specific deployment service."""
        deployment = await self.get_deployment(deployment_id, user_id)
        if not deployment:
            raise ValueError("Deployment record not found or access denied.")

        svc = next((s for s in deployment.services if s.service_id == service_id), None)
        if not svc or not svc.container_name:
            raise ValueError(f"Service '{service_id}' not found in deployment.")

        service_mgr = ServiceManager(DockerRuntime())
        return service_mgr.get_service_logs(svc.container_name, limit=limit)


async def run_background_deployment(deployment_id: uuid.UUID) -> None:
    """Background worker task executing full container orchestration pipeline."""
    async with AsyncSessionLocal() as session:
        deployment_repo = DeploymentRepository(session)
        plan_repo = PlanRepository(session)
        analysis_repo = AnalysisRepository(session)

        deployment = await deployment_repo.get(deployment_id)
        if not deployment:
            logger.error(f"Background deployment task failed: deployment_id {deployment_id} not found")
            return

        plan_record = await plan_repo.get(deployment.infrastructure_plan_id)
        if not plan_record or not plan_record.plan_data:
            await deployment_repo.update_status(deployment_id, status=DeploymentStatus.FAILED, error_message="Plan data missing.")
            return

        plan = InfrastructurePlan.model_validate(plan_record.plan_data)
        analysis = await analysis_repo.get(plan_record.repository_analysis_id)
        repo_workspace = getattr(analysis, "workspace_path", None) if analysis else None

        engine = DeploymentEngine()
        await engine.execute_deployment(
            deployment_id=deployment_id,
            project_id=deployment.project_id,
            plan=plan,
            repo_workspace_path=repo_workspace,
            deployment_repo=deployment_repo,
            version=deployment.version,
        )
