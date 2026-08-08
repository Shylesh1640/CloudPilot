"""ImageManager — handles pulling prebuilt images and building app Dockerfiles."""
from __future__ import annotations

import os
from pathlib import Path
import uuid
from typing import Any

from app.services.ai.schemas import ServiceDefinition
from app.services.orchestrator.docker_client import ContainerRuntime
from app.services.orchestrator.exceptions import DeploymentBlockedError
from app.services.orchestrator.utils import make_image_name


class ImageManager:
    def __init__(self, runtime: ContainerRuntime) -> None:
        self.runtime = runtime

    def prepare_service_image(
        self,
        project_id: uuid.UUID,
        service: ServiceDefinition,
        repo_workspace_path: str | None = None,
        deployment_version: int = 1,
    ) -> str:
        """
        Pulls pre-built image (e.g. database/cache) or builds Dockerfile for app service.
        Returns final Docker image string tag.
        """
        svc_type = service.type.lower()

        # Mode A: Known Prebuilt Infrastructure Images
        if svc_type == "database":
            img_name = f"{service.name.lower()}:16-alpine" if "postg" in service.name.lower() else "mysql:8-oracle"
            self.runtime.pull_image(img_name)
            return img_name
        elif svc_type == "cache":
            img_name = "redis:7-alpine"
            self.runtime.pull_image(img_name)
            return img_name
        elif svc_type == "queue":
            img_name = "rabbitmq:3-management-alpine"
            self.runtime.pull_image(img_name)
            return img_name

        # Mode B: Build from Repository Workspace Dockerfile
        target_image_tag = make_image_name(project_id, service.id, version=deployment_version)

        if not repo_workspace_path or not os.path.exists(repo_workspace_path):
            # Fallback to lightweight alpine for mock/test runs if workspace missing
            return "alpine:latest"

        workspace = Path(repo_workspace_path)
        # Search for Dockerfile in service source_path or root
        candidate_paths = [
            workspace / service.source_path.lstrip("/") / "Dockerfile" if service.source_path else None,
            workspace / "Dockerfile",
            workspace / service.id / "Dockerfile",
        ]
        dockerfile_path = None
        for path in candidate_paths:
            if path and path.exists() and path.is_file():
                dockerfile_path = path
                break

        if not dockerfile_path:
            raise DeploymentBlockedError(
                f"No Dockerfile detected for application service '{service.name}' ({service.id}). "
                f"Application deployment requires a valid Dockerfile in the repository.",
                code="DEPLOYMENT_BLOCKED",
            )

        build_context_dir = str(dockerfile_path.parent)
        dockerfile_filename = dockerfile_path.name

        self.runtime.build_image(
            path=build_context_dir,
            tag=target_image_tag,
            dockerfile=dockerfile_filename,
        )
        return target_image_tag
