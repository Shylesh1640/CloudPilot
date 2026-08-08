"""ServiceManager — high-level container service operations (restart, stop, logs)."""
from __future__ import annotations

import logging
from app.services.orchestrator.docker_client import ContainerRuntime

logger = logging.getLogger("cloudpilot.service_manager")


class ServiceManager:
    def __init__(self, runtime: ContainerRuntime) -> None:
        self.runtime = runtime

    def restart_service(self, container_name_or_id: str) -> None:
        logger.info(f"Restarting service container '{container_name_or_id}'")
        self.runtime.restart_container(container_name_or_id)

    def stop_service(self, container_name_or_id: str) -> None:
        logger.info(f"Stopping service container '{container_name_or_id}'")
        self.runtime.stop_container(container_name_or_id)

    def get_service_logs(self, container_name_or_id: str, limit: int = 200) -> str:
        logger.info(f"Fetching logs for service container '{container_name_or_id}' (limit={limit})")
        return self.runtime.get_container_logs(container_name_or_id, tail=limit)
