"""VolumeManager — handles persistent Docker volume creation."""
from __future__ import annotations

import uuid
from app.services.ai.schemas import VolumeDefinition
from app.services.orchestrator.docker_client import ContainerRuntime
from app.services.orchestrator.utils import build_cloudpilot_labels, make_volume_name


class VolumeManager:
    def __init__(self, runtime: ContainerRuntime) -> None:
        self.runtime = runtime

    def prepare_volumes(
        self,
        project_id: uuid.UUID,
        deployment_id: uuid.UUID,
        volumes: list[VolumeDefinition],
    ) -> dict[str, str]:
        """
        Creates Docker volumes for persistent storage definitions in the infrastructure plan.
        Returns mapping: service_id -> volume_name.
        """
        vol_map: dict[str, str] = {}
        for vol in volumes:
            if not vol.persistent:
                continue

            vol_name = make_volume_name(project_id, vol.service)
            labels = build_cloudpilot_labels(
                project_id=project_id,
                deployment_id=deployment_id,
                service_id=vol.service,
                resource_type="volume",
            )
            self.runtime.create_volume(vol_name, labels=labels)
            vol_map[vol.service] = vol_name

        return vol_map
