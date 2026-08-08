"""Docker SDK abstraction layer encapsulating all container runtime operations."""
from __future__ import annotations

import abc
import logging
from typing import Any

from app.services.orchestrator.exceptions import DockerConnectionError, OrchestratorError

logger = logging.getLogger("cloudpilot.docker_client")


class ContainerRuntime(abc.ABC):
    """Abstract interface for container runtime backends."""

    @abc.abstractmethod
    def ping(self) -> bool:
        pass

    @abc.abstractmethod
    def create_network(self, name: str, labels: dict[str, str] | None = None) -> Any:
        pass

    @abc.abstractmethod
    def remove_network(self, name: str) -> None:
        pass

    @abc.abstractmethod
    def create_volume(self, name: str, labels: dict[str, str] | None = None) -> Any:
        pass

    @abc.abstractmethod
    def remove_volume(self, name: str) -> None:
        pass

    @abc.abstractmethod
    def pull_image(self, image: str) -> Any:
        pass

    @abc.abstractmethod
    def build_image(self, path: str, tag: str, dockerfile: str = "Dockerfile", buildargs: dict[str, str] | None = None) -> Any:
        pass

    @abc.abstractmethod
    def create_container(
        self,
        image: str,
        name: str,
        network: str,
        environment: dict[str, str] | None = None,
        volumes: dict[str, dict[str, str]] | None = None,
        ports: dict[str, int] | None = None,
        labels: dict[str, str] | None = None,
        cpu_limit: str | None = None,
        mem_limit: str | None = None,
    ) -> str:
        pass

    @abc.abstractmethod
    def start_container(self, container_id_or_name: str) -> None:
        pass

    @abc.abstractmethod
    def stop_container(self, container_id_or_name: str, timeout: int = 10) -> None:
        pass

    @abc.abstractmethod
    def restart_container(self, container_id_or_name: str, timeout: int = 10) -> None:
        pass

    @abc.abstractmethod
    def remove_container(self, container_id_or_name: str, force: bool = True) -> None:
        pass

    @abc.abstractmethod
    def inspect_container(self, container_id_or_name: str) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def get_container_logs(self, container_id_or_name: str, tail: int = 200) -> str:
        pass


class DockerRuntime(ContainerRuntime):
    """Production implementation using official docker Python SDK."""

    def __init__(self) -> None:
        self._client = None
        self._init_client()

    def _init_client() -> None:
        try:
            import docker
            self._client = docker.from_env()
        except Exception as err:
            logger.warning(f"Failed to connect to local Docker daemon: {err}")
            self._client = None

    @property
    def is_connected(self) -> bool:
        if self._client is None:
            return False
        try:
            return self._client.ping()
        except Exception:
            return False

    def ping(self) -> bool:
        return self.is_connected

    def create_network(self, name: str, labels: dict[str, str] | None = None) -> Any:
        if not self._client:
            logger.info(f"[MOCK DOCKER] create_network('{name}')")
            return {"name": name, "id": f"net-{name}"}

        try:
            # Idempotent check
            existing = self._client.networks.list(names=[name])
            if existing:
                logger.info(f"Docker network '{name}' already exists. Reusing.")
                return existing[0]

            logger.info(f"Creating Docker network '{name}'")
            return self._client.networks.create(name, driver="bridge", labels=labels or {})
        except Exception as err:
            raise OrchestratorError(f"Failed to create Docker network '{name}': {err}")

    def remove_network(self, name: str) -> None:
        if not self._client:
            logger.info(f"[MOCK DOCKER] remove_network('{name}')")
            return

        try:
            existing = self._client.networks.list(names=[name])
            if existing:
                existing[0].remove()
        except Exception as err:
            logger.warning(f"Error removing network '{name}': {err}")

    def create_volume(self, name: str, labels: dict[str, str] | None = None) -> Any:
        if not self._client:
            logger.info(f"[MOCK DOCKER] create_volume('{name}')")
            return {"name": name}

        try:
            logger.info(f"Creating Docker volume '{name}'")
            return self._client.volumes.create(name=name, labels=labels or {})
        except Exception as err:
            raise OrchestratorError(f"Failed to create Docker volume '{name}': {err}")

    def remove_volume(self, name: str) -> None:
        if not self._client:
            logger.info(f"[MOCK DOCKER] remove_volume('{name}')")
            return

        try:
            vol = self._client.volumes.get(name)
            vol.remove(force=True)
        except Exception as err:
            logger.warning(f"Error removing volume '{name}': {err}")

    def pull_image(self, image: str) -> Any:
        if not self._client:
            logger.info(f"[MOCK DOCKER] pull_image('{image}')")
            return {"image": image}

        try:
            logger.info(f"Pulling Docker image '{image}'")
            return self._client.images.pull(image)
        except Exception as err:
            raise OrchestratorError(f"Failed to pull image '{image}': {err}")

    def build_image(self, path: str, tag: str, dockerfile: str = "Dockerfile", buildargs: dict[str, str] | None = None) -> Any:
        if not self._client:
            logger.info(f"[MOCK DOCKER] build_image(path='{path}', tag='{tag}')")
            return {"tag": tag}

        try:
            logger.info(f"Building Docker image '{tag}' from path '{path}' ({dockerfile})")
            img, _logs = self._client.images.build(
                path=path,
                dockerfile=dockerfile,
                tag=tag,
                buildargs=buildargs or {},
                rm=True,
            )
            return img
        except Exception as err:
            raise OrchestratorError(f"Failed to build Docker image '{tag}': {err}")

    def create_container(
        self,
        image: str,
        name: str,
        network: str,
        environment: dict[str, str] | None = None,
        volumes: dict[str, dict[str, str]] | None = None,
        ports: dict[str, int] | None = None,
        labels: dict[str, str] | None = None,
        cpu_limit: str | None = None,
        mem_limit: str | None = None,
    ) -> str:
        if not self._client:
            logger.info(f"[MOCK DOCKER] create_container(name='{name}', image='{image}')")
            return f"mock-container-id-{name}"

        try:
            # Idempotent cleanup of existing container with same name if present
            try:
                old = self._client.containers.get(name)
                old.remove(force=True)
            except Exception:
                pass

            # Resource constraints
            extra_kwargs: dict[str, Any] = {}
            if mem_limit:
                # e.g., "512Mi" -> 536870912 bytes
                if mem_limit.endswith("Mi"):
                    extra_kwargs["mem_limit"] = int(mem_limit[:-2]) * 1024 * 1024
                elif mem_limit.endswith("Gi"):
                    extra_kwargs["mem_limit"] = int(mem_limit[:-2]) * 1024 * 1024 * 1024

            container = self._client.containers.create(
                image=image,
                name=name,
                network=network,
                environment=environment or {},
                volumes=volumes or {},
                ports=ports or {},
                labels=labels or {},
                detach=True,
                **extra_kwargs,
            )
            return container.id
        except Exception as err:
            raise OrchestratorError(f"Failed to create container '{name}': {err}")

    def start_container(self, container_id_or_name: str) -> None:
        if not self._client:
            logger.info(f"[MOCK DOCKER] start_container('{container_id_or_name}')")
            return

        try:
            c = self._client.containers.get(container_id_or_name)
            c.start()
        except Exception as err:
            raise OrchestratorError(f"Failed to start container '{container_id_or_name}': {err}")

    def stop_container(self, container_id_or_name: str, timeout: int = 10) -> None:
        if not self._client:
            logger.info(f"[MOCK DOCKER] stop_container('{container_id_or_name}')")
            return

        try:
            c = self._client.containers.get(container_id_or_name)
            c.stop(timeout=timeout)
        except Exception as err:
            raise OrchestratorError(f"Failed to stop container '{container_id_or_name}': {err}")

    def restart_container(self, container_id_or_name: str, timeout: int = 10) -> None:
        if not self._client:
            logger.info(f"[MOCK DOCKER] restart_container('{container_id_or_name}')")
            return

        try:
            c = self._client.containers.get(container_id_or_name)
            c.restart(timeout=timeout)
        except Exception as err:
            raise OrchestratorError(f"Failed to restart container '{container_id_or_name}': {err}")

    def remove_container(self, container_id_or_name: str, force: bool = True) -> None:
        if not self._client:
            logger.info(f"[MOCK DOCKER] remove_container('{container_id_or_name}')")
            return

        try:
            c = self._client.containers.get(container_id_or_name)
            c.remove(force=force)
        except Exception as err:
            logger.warning(f"Error removing container '{container_id_or_name}': {err}")

    def inspect_container(self, container_id_or_name: str) -> dict[str, Any]:
        if not self._client:
            logger.info(f"[MOCK DOCKER] inspect_container('{container_id_or_name}')")
            return {"State": {"Status": "running", "Running": True}, "Name": f"/{container_id_or_name}"}

        try:
            c = self._client.containers.get(container_id_or_name)
            return c.attrs
        except Exception:
            return {"State": {"Status": "unknown", "Running": False}}

    def get_container_logs(self, container_id_or_name: str, tail: int = 200) -> str:
        if not self._client:
            return f"[MOCK DOCKER LOGS] Container {container_id_or_name} started successfully.\nService running."

        try:
            c = self._client.containers.get(container_id_or_name)
            logs_bytes = c.logs(tail=tail, stdout=True, stderr=True)
            return logs_bytes.decode("utf-8", errors="replace")
        except Exception as err:
            return f"Failed to retrieve container logs: {err}"
