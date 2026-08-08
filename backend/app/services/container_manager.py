"""
Container Manager Service — Phase 4 Stub.

This service will manage Docker container lifecycle:
- Build Docker images from repository source
- Push images to a container registry
- Pull and run containers on target hosts
- Manage container networking and volumes

Implementation is deferred to Phase 4: Container Manager.
"""
from __future__ import annotations


class ContainerManager:
    """
    Manages the full container image lifecycle.

    Phase 4 will implement:
    - Docker SDK integration
    - Image build from Dockerfile or auto-generated Dockerfile
    - Registry push/pull operations
    - Container start/stop/restart
    - Log streaming
    """

    async def build_image(self, project_id: str, source_path: str) -> str:
        """
        Build a Docker image for the project.

        Args:
            project_id: The CloudPilot project ID.
            source_path: Path to the source code directory.

        Returns:
            Image tag (e.g., 'cloudpilot/my-app:abc123').

        Raises:
            NotImplementedError: Until Phase 4 is implemented.
        """
        raise NotImplementedError("Container management is implemented in Phase 4.")

    async def run_container(self, image_tag: str, config: dict) -> str:
        """
        Start a container from a built image.

        Returns:
            Container ID.

        Raises:
            NotImplementedError: Until Phase 4 is implemented.
        """
        raise NotImplementedError("Container management is implemented in Phase 4.")
