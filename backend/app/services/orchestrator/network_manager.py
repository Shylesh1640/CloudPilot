"""NetworkManager — handles isolated Docker bridge network creation and teardown."""
from __future__ import annotations

import uuid
from app.services.orchestrator.docker_client import ContainerRuntime
from app.services.orchestrator.utils import build_cloudpilot_labels, make_network_name


class NetworkManager:
    def __init__(self, runtime: ContainerRuntime) -> None:
        self.runtime = runtime

    def create_project_network(self, project_id: uuid.UUID, deployment_id: uuid.UUID) -> str:
        """Create or reuse an isolated Docker bridge network for the project."""
        network_name = make_network_name(project_id)
        labels = build_cloudpilot_labels(
            project_id=project_id,
            deployment_id=deployment_id,
            service_id="network",
            resource_type="network",
        )
        self.runtime.create_network(network_name, labels=labels)
        return network_name
