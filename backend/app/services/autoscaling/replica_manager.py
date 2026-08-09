"""Safe horizontal replica convergence through the Phase 4 runtime abstraction."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deployment import DeploymentServiceModel, ServiceActualState, ServiceDesiredState
from app.services.orchestrator.docker_client import ContainerRuntime
from app.services.orchestrator.utils import build_cloudpilot_labels, make_network_name


class ReplicaManager:
    def __init__(self, session: AsyncSession, runtime: ContainerRuntime) -> None:
        self.session = session
        self.runtime = runtime

    async def replicas(self, deployment_id: uuid.UUID, service_id: str) -> list[DeploymentServiceModel]:
        result = await self.session.execute(select(DeploymentServiceModel).where(DeploymentServiceModel.deployment_id == deployment_id, DeploymentServiceModel.service_id == service_id).order_by(DeploymentServiceModel.replica_id))
        return list(result.scalars())

    async def get_current_replicas(self, deployment_id: uuid.UUID, service_id: str) -> int:
        return len(await self.replicas(deployment_id, service_id))

    async def scale_to(self, deployment, service_id: str, replicas: int) -> int:
        records = await self.replicas(deployment.id, service_id)
        if len(records) == replicas:
            return len(records)
        if not records:
            raise ValueError(f"Service '{service_id}' has no managed runtime record.")
        for record in records:
            record.desired_replicas = replicas
        if len(records) < replicas:
            template = records[0]
            existing_ids = {r.replica_id for r in records}
            for replica_id in range(1, replicas + 1):
                if replica_id in existing_ids:
                    continue
                name = f"cloudpilot-{str(deployment.project_id).replace('-', '')[:8]}-{service_id}-{replica_id}"
                labels = build_cloudpilot_labels(deployment.project_id, deployment.id, service_id, "container")
                labels["cloudpilot.replica_id"] = str(replica_id)
                container_id = self.runtime.create_container(image=template.image, name=name, network=make_network_name(deployment.project_id), ports={}, labels=labels)
                self.runtime.start_container(container_id)
                runtime_state = self.runtime.inspect_container(container_id).get("State", {}).get("Status", "starting").lower()
                actual_state = ServiceActualState.RUNNING if runtime_state == "running" else ServiceActualState.STARTING
                self.session.add(DeploymentServiceModel(deployment_id=deployment.id, service_id=service_id, container_id=container_id, container_name=name, image=template.image, desired_state=ServiceDesiredState.RUNNING, actual_state=actual_state, status="RUNNING" if actual_state == ServiceActualState.RUNNING else "STARTING", port=template.port, public=False, desired_replicas=replicas, replica_id=replica_id))
        else:
            # Newest healthy/running replica first; never removes the primary routing record.
            for record in sorted(records, key=lambda r: r.replica_id, reverse=True)[: len(records) - replicas]:
                if record.replica_id == 1 and len(records) > 1:
                    continue
                self.runtime.stop_container(record.container_id or record.container_name)
                self.runtime.remove_container(record.container_id or record.container_name)
                await self.session.delete(record)
        await self.session.commit()
        return await self.get_current_replicas(deployment.id, service_id)

    async def reconcile(self, deployment, service_id: str, desired_replicas: int) -> int:
        return await self.scale_to(deployment, service_id, desired_replicas)
