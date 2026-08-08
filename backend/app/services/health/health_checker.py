"""Unified HealthChecker dispatching HTTP, TCP, or Container health check routines."""
from __future__ import annotations

import logging
from app.models.health import HealthStatus
from app.services.ai.schemas import ServiceDefinition
from app.services.health.container_checker import ContainerChecker
from app.services.health.http_checker import HTTPChecker
from app.services.health.models import HealthCheckResult
from app.services.health.tcp_checker import TCPChecker
from app.services.orchestrator import ContainerRuntime, DockerRuntime

logger = logging.getLogger("cloudpilot.health_checker")


class HealthChecker:
    """Dispatches service health checks using HTTP, TCP, or Container runtime inspectors."""

    def __init__(self, runtime: ContainerRuntime | None = None) -> None:
        self.http_checker = HTTPChecker()
        self.tcp_checker = TCPChecker()
        self.container_checker = ContainerChecker(runtime or DockerRuntime())

    async def check_service_health(
        self,
        service: ServiceDefinition,
        container_name: str,
        network_host_alias: str | None = None,
        health_check_path: str | None = None,
        health_check_port: int | None = None,
        timeout_seconds: int = 3,
    ) -> HealthCheckResult:
        """
        Executes primary check according to fallback chain:
        1. Container Runtime Check (if container exited -> FAILED immediately)
        2. HTTP Check (if health_check_path or HTTP port configured)
        3. TCP Check (if service has port)
        4. Container Check (fallback)
        """
        # Step 1: Raw container check first
        container_res = self.container_checker.check(service.id, container_name)
        if container_res.status == HealthStatus.FAILED:
            return container_res

        target_host = network_host_alias or container_name
        svc_type = service.type.lower()
        target_port = health_check_port or service.port

        # Step 2: HTTP Check if path or public application
        if health_check_path or (svc_type == "application" and target_port):
            http_path = health_check_path or "/health"
            return await self.http_checker.check(
                service_id=service.id,
                host=target_host,
                port=target_port or 8000,
                path=http_path,
                timeout_seconds=timeout_seconds,
            )

        # Step 3: TCP Check if port defined
        if target_port:
            return await self.tcp_checker.check(
                service_id=service.id,
                host=target_host,
                port=target_port,
                timeout_seconds=timeout_seconds,
            )

        # Step 4: Fallback Container check
        return container_res
