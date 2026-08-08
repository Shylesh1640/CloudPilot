"""Internal Pydantic models for orchestration management."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class CloudPilotLabels(BaseModel):
    managed: str = "true"
    project_id: str
    deployment_id: str
    service_id: str
    resource_type: Literal["container", "network", "volume"]

    def to_dict(self) -> dict[str, str]:
        return {
            "cloudpilot.managed": self.managed,
            "cloudpilot.project_id": self.project_id,
            "cloudpilot.deployment_id": self.deployment_id,
            "cloudpilot.service_id": self.service_id,
            "cloudpilot.resource_type": self.resource_type,
        }


class ContainerSpec(BaseModel):
    service_id: str
    container_name: str
    image: str
    network_name: str
    environment: dict[str, str] = Field(default_factory=dict)
    volumes: dict[str, dict[str, str]] = Field(default_factory=dict)  # vol_name -> {'bind': mount_path, 'mode': 'rw'}
    ports: dict[str, int] = Field(default_factory=dict)                # container_port/tcp -> host_port
    cpu_limit: str | None = None
    mem_limit: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    restart_policy: dict[str, Any] = Field(default_factory=lambda: {"Name": "unless-stopped"})
