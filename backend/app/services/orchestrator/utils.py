"""Utility functions for container naming, label generation, and validation."""
from __future__ import annotations

import re
import uuid
from app.services.orchestrator.models import CloudPilotLabels


def get_short_id(val: str | uuid.UUID) -> str:
    """Return an 8-character clean alphanumeric hex identifier."""
    raw = str(val).replace("-", "").lower()
    return raw[:8]


def make_network_name(project_id: uuid.UUID) -> str:
    """Generate isolated network name: cloudpilot-<project_short>-net."""
    return f"cloudpilot-{get_short_id(project_id)}-net"


def make_volume_name(project_id: uuid.UUID, service_id: str) -> str:
    """Generate persistent volume name: cloudpilot-<project_short>-<service_id>-data."""
    clean_svc = re.sub(r"[^a-zA-Z0-9_-]", "", service_id.lower())
    return f"cloudpilot-{get_short_id(project_id)}-{clean_svc}-data"


def make_container_name(project_id: uuid.UUID, service_id: str, version: int = 1) -> str:
    """Generate container name: cloudpilot-<project_short>-<service_id>-v<version>."""
    clean_svc = re.sub(r"[^a-zA-Z0-9_-]", "", service_id.lower())
    return f"cloudpilot-{get_short_id(project_id)}-{clean_svc}-v{version}"


def make_image_name(project_id: uuid.UUID, service_id: str, version: int = 1) -> str:
    """Generate Docker image name: cloudpilot/<project_short>/<service_id>:v<version>."""
    clean_svc = re.sub(r"[^a-zA-Z0-9_-]", "", service_id.lower())
    return f"cloudpilot/{get_short_id(project_id)}/{clean_svc}:v{version}"


def build_cloudpilot_labels(
    project_id: uuid.UUID,
    deployment_id: uuid.UUID,
    service_id: str,
    resource_type: str,
) -> dict[str, str]:
    """Return dictionary of CloudPilot ownership labels."""
    labels = CloudPilotLabels(
        project_id=str(project_id),
        deployment_id=str(deployment_id),
        service_id=service_id,
        resource_type=resource_type,  # type: ignore
    )
    return labels.to_dict()
