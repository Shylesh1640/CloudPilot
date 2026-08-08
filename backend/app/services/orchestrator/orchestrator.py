"""DeploymentEngine — Master orchestrator workflow manager."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.models.deployment import DeploymentStatus, ServiceActualState, ServiceDesiredState
from app.repositories.deployment_repository import DeploymentRepository
from app.services.ai.schemas import InfrastructurePlan
from app.services.orchestrator.container_manager import ContainerManager
from app.services.orchestrator.dependency_manager import DependencyManager
from app.services.orchestrator.deployment_state import DeploymentStateReconciler
from app.services.orchestrator.docker_client import ContainerRuntime, DockerRuntime
from app.services.orchestrator.exceptions import OrchestratorError
from app.services.orchestrator.image_manager import ImageManager
from app.services.orchestrator.network_manager import NetworkManager
from app.services.orchestrator.service_manager import ServiceManager
from app.services.orchestrator.volume_manager import VolumeManager

logger = logging.getLogger("cloudpilot.orchestrator")


class DeploymentEngine:
    """Master Orchestrator Engine executing Phase 4 container deployment workflow."""

    def __init__(self, runtime: ContainerRuntime | None = None) -> None:
        self.runtime = runtime or DockerRuntime()
        self.network_mgr = NetworkManager(self.runtime)
        self.volume_mgr = VolumeManager(self.runtime)
        self.image_mgr = ImageManager(self.runtime)
        self.container_mgr = ContainerManager(self.runtime)
        self.service_mgr = ServiceManager(self.runtime)
        self.reconciler = DeploymentStateReconciler(self.runtime)

    async def execute_deployment(
        self,
        deployment_id: uuid.UUID,
        project_id: uuid.UUID,
        plan: InfrastructurePlan,
        repo_workspace_path: str | None,
        deployment_repo: DeploymentRepository,
        version: int = 1,
    ) -> None:
        """Executes full step-by-step container orchestration pipeline."""
        logger.info(f"Starting orchestration pipeline for deployment {deployment_id} (project {project_id})")

        try:
            # 1. Validate dependencies & compute startup order
            await deployment_repo.update_status(
                deployment_id,
                status=DeploymentStatus.PREPARING,
                progress=10,
                log_entry="Validating service dependency topology...",
            )
            execution_order = DependencyManager.get_execution_order(plan)

            # 2. Create isolated Docker bridge network
            await deployment_repo.update_status(
                deployment_id,
                status=DeploymentStatus.CREATING_NETWORK,
                progress=25,
                log_entry="Creating isolated project network...",
            )
            network_name = self.network_mgr.create_project_network(project_id, deployment_id)

            # 3. Create persistent volumes
            await deployment_repo.update_status(
                deployment_id,
                status=DeploymentStatus.CREATING_VOLUMES,
                progress=40,
                log_entry="Creating persistent storage volumes...",
            )
            volume_map = self.volume_mgr.prepare_volumes(project_id, deployment_id, plan.volumes)

            # 4. Image Preparation (Pull prebuilt & Build app Dockerfiles)
            await deployment_repo.update_status(
                deployment_id,
                status=DeploymentStatus.BUILDING,
                progress=55,
                log_entry="Preparing container images (pulling prebuilt & building app Dockerfiles)...",
            )
            image_map: dict[str, str] = {}
            service_dict = {s.id: s for s in plan.services}

            for sid in execution_order:
                svc = service_dict[sid]
                img_tag = self.image_mgr.prepare_service_image(
                    project_id=project_id,
                    service=svc,
                    repo_workspace_path=repo_workspace_path,
                    deployment_version=version,
                )
                image_map[sid] = img_tag

            # 5. Create & Start Containers in topological order
            await deployment_repo.update_status(
                deployment_id,
                status=DeploymentStatus.CREATING_SERVICES,
                progress=75,
                log_entry="Instantiating containers and starting services...",
            )

            total_services = len(execution_order)
            for idx, sid in enumerate(execution_order):
                svc = service_dict[sid]
                img_tag = image_map[sid]

                spec = self.container_mgr.prepare_container_spec(
                    project_id=project_id,
                    deployment_id=deployment_id,
                    service=svc,
                    image=img_tag,
                    network_name=network_name,
                    plan=plan,
                    volume_map=volume_map,
                    version=version,
                )

                # Record DB service entry
                svc_record = await deployment_repo.add_service(
                    deployment_id=deployment_id,
                    service_id=svc.id,
                    container_name=spec.container_name,
                    image=img_tag,
                    port=svc.port,
                    public=svc.public,
                )

                # Create & Start container
                container_id = self.container_mgr.create_and_start(spec)

                # Inspect actual state
                actual_state, raw_status = self.reconciler.inspect_actual_state(container_id)

                await deployment_repo.update_service_state(
                    svc_record.id,
                    container_id=container_id,
                    desired_state=ServiceDesiredState.RUNNING,
                    actual_state=actual_state,
                    status="RUNNING" if actual_state == ServiceActualState.RUNNING else raw_status.upper(),
                )

                current_progress = 75 + int(((idx + 1) / total_services) * 20)
                await deployment_repo.update_status(
                    deployment_id,
                    status=DeploymentStatus.STARTING,
                    progress=current_progress,
                    log_entry=f"Service '{svc.name}' ({spec.container_name}) started successfully.",
                )

            # 6. Mark Deployment RUNNING
            await deployment_repo.update_status(
                deployment_id,
                status=DeploymentStatus.RUNNING,
                progress=100,
                log_entry="All services successfully orchestrated and running.",
            )
            logger.info(f"Deployment {deployment_id} completed successfully.")

        except OrchestratorError as err:
            logger.warning(f"Orchestration failed for deployment {deployment_id}: [{err.code}] {err.message}")
            await deployment_repo.update_status(
                deployment_id,
                status=DeploymentStatus.FAILED,
                error_message=err.message,
                log_entry=f"DEPLOYMENT FAILED: {err.message}",
            )
        except Exception as exc:
            logger.exception(f"Unexpected orchestration failure for deployment {deployment_id}: {exc}")
            await deployment_repo.update_status(
                deployment_id,
                status=DeploymentStatus.FAILED,
                error_message="An unexpected error occurred during container orchestration.",
                log_entry="DEPLOYMENT FAILED: Unexpected error.",
            )
