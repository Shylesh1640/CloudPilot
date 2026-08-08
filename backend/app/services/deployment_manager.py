"""
Deployment Manager Service — Phase 5 Stub.

This service will orchestrate full deployment workflows:
- Coordinate build → push → run pipeline
- Track deployment status and rollout progress
- Support blue/green and rolling deployments
- Handle rollback on failure

Implementation is deferred to Phase 5: Deployment Engine.
"""
from __future__ import annotations


class DeploymentManager:
    """
    Orchestrates end-to-end deployment pipelines.

    Phase 5 will implement:
    - Deployment pipeline state machine
    - Integration with ContainerManager
    - Health-check gating before traffic switch
    - Deployment history tracking
    - Rollback support
    """

    async def deploy(self, project_id: str, image_tag: str) -> str:
        """
        Start a deployment pipeline.

        Args:
            project_id: The CloudPilot project ID.
            image_tag: Container image to deploy.

        Returns:
            Deployment ID.

        Raises:
            NotImplementedError: Until Phase 5 is implemented.
        """
        raise NotImplementedError("Deployment management is implemented in Phase 5.")

    async def rollback(self, deployment_id: str) -> None:
        """
        Roll back a deployment to the previous version.

        Raises:
            NotImplementedError: Until Phase 5 is implemented.
        """
        raise NotImplementedError("Deployment rollback is implemented in Phase 5.")
