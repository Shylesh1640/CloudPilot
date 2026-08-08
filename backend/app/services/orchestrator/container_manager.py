"""ContainerManager — creates and manages individual container instances."""
from __future__ import annotations

import uuid
from typing import Any

from app.services.ai.schemas import InfrastructurePlan, ServiceDefinition
from app.services.orchestrator.docker_client import ContainerRuntime
from app.services.orchestrator.models import ContainerSpec
from app.services.orchestrator.utils import build_cloudpilot_labels, make_container_name


class ContainerManager:
    def __init__(self, runtime: ContainerRuntime) -> None:
        self.runtime = runtime

    def prepare_container_spec(
        self,
        project_id: uuid.UUID,
        deployment_id: uuid.UUID,
        service: ServiceDefinition,
        image: str,
        network_name: str,
        plan: InfrastructurePlan,
        volume_map: dict[str, str],
        version: int = 1,
    ) -> ContainerSpec:
        container_name = make_container_name(project_id, service.id, version)

        # Environment variables
        env_dict: dict[str, str] = {}
        # Add internal service discovery variables
        for dep in plan.dependencies:
            if dep.source == service.id:
                target_svc = plan.services_by_id().get(dep.target) if hasattr(plan, 'services_by_id') else None
                dep_type = dep.dependency_type.upper()
                env_dict[f"{dep.target.upper()}_HOST"] = dep.target
                if dep_type == "DATABASE":
                    env_dict["DATABASE_HOST"] = dep.target
                    env_dict["DATABASE_PORT"] = "5432"
                elif dep_type == "CACHE":
                    env_dict["REDIS_HOST"] = dep.target
                    env_dict["REDIS_PORT"] = "6379"

        # Explicit environment group from plan
        env_grp = next((e for e in plan.environment if e.service == service.id), None)
        if env_grp:
            for v in env_grp.variables:
                val = v.default or ("${" + v.name + "}" if v.secret else "")
                env_dict[v.name] = val

        # Ports: ONLY public services publish host ports
        ports_dict: dict[str, int] = {}
        if service.public and service.port:
            container_port_key = f"{service.port}/tcp"
            ports_dict[container_port_key] = service.port

        # Volumes
        vols_dict: dict[str, dict[str, str]] = {}
        if service.id in volume_map:
            vol_name = volume_map[service.id]
            vol_def = next((v for v in plan.volumes if v.service == service.id), None)
            mount_path = vol_def.mount_path if vol_def else "/data"
            vols_dict[vol_name] = {"bind": mount_path, "mode": "rw"}

        # Resource limits from profile
        res_prof = next((r for r in plan.resource_profiles if r.service == service.id), None)
        cpu_limit = res_prof.cpu if res_prof else "0.5"
        mem_limit = res_prof.memory if res_prof else "512Mi"

        labels = build_cloudpilot_labels(
            project_id=project_id,
            deployment_id=deployment_id,
            service_id=service.id,
            resource_type="container",
        )

        return ContainerSpec(
            service_id=service.id,
            container_name=container_name,
            image=image,
            network_name=network_name,
            environment=env_dict,
            volumes=vols_dict,
            ports=ports_dict,
            cpu_limit=cpu_limit,
            mem_limit=mem_limit,
            labels=labels,
        )

    def create_and_start(self, spec: ContainerSpec) -> str:
        """Create container on Docker runtime and start it."""
        container_id = self.runtime.create_container(
            image=spec.image,
            name=spec.container_name,
            network=spec.network_name,
            environment=spec.environment,
            volumes=spec.volumes,
            ports=spec.ports,
            labels=spec.labels,
            cpu_limit=spec.cpu_limit,
            mem_limit=spec.mem_limit,
        )
        self.runtime.start_container(container_id)
        return container_id
