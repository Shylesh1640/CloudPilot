"""Exceptions for Container & Service Orchestrator."""
from __future__ import annotations


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""
    code: str = "ORCHESTRATOR_ERROR"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message


class DockerConnectionError(OrchestratorError):
    code = "DOCKER_CONNECTION_ERROR"


class ImageBuildError(OrchestratorError):
    code = "IMAGE_BUILD_ERROR"


class DeploymentBlockedError(OrchestratorError):
    code = "DEPLOYMENT_BLOCKED"


class ResourceConflictError(OrchestratorError):
    code = "RESOURCE_CONFLICT"


class ContainerExecutionError(OrchestratorError):
    code = "CONTAINER_EXECUTION_ERROR"
