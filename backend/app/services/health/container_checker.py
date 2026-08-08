"""Container Health Checker inspecting Docker container runtime process state."""
from __future__ import annotations

import datetime
import logging
from app.models.health import HealthStatus
from app.services.health.models import HealthCheckResult
from app.services.orchestrator import ContainerRuntime, DockerRuntime

logger = logging.getLogger("cloudpilot.container_checker")


class ContainerChecker:
    def __init__(self, runtime: ContainerRuntime | None = None) -> None:
        self.runtime = runtime or DockerRuntime()

    def check(
        self,
        service_id: str,
        container_name_or_id: str,
    ) -> HealthCheckResult:
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        info = self.runtime.inspect_container(container_name_or_id)
        state_dict = info.get("State", {})
        running = state_dict.get("Running", False)
        status_str = state_dict.get("Status", "unknown").lower()
        restart_count = state_dict.get("RestartCount", 0)

        if running and status_str in ("running",):
            if restart_count > 5:
                return HealthCheckResult(
                    service_id=service_id,
                    check_type="CONTAINER",
                    status=HealthStatus.DEGRADED,
                    error_message=f"Container running but flapping (restart_count={restart_count})",
                    timestamp=timestamp_str,
                )
            return HealthCheckResult(
                service_id=service_id,
                check_type="CONTAINER",
                status=HealthStatus.HEALTHY,
                status_code=0,
                timestamp=timestamp_str,
            )
        elif status_str in ("exited", "dead"):
            exit_code = state_dict.get("ExitCode", 1)
            return HealthCheckResult(
                service_id=service_id,
                check_type="CONTAINER",
                status=HealthStatus.FAILED,
                status_code=exit_code,
                error_message=f"Container exited with exit code {exit_code}",
                timestamp=timestamp_str,
            )
        else:
            return HealthCheckResult(
                service_id=service_id,
                check_type="CONTAINER",
                status=HealthStatus.STARTING,
                error_message=f"Container status is '{status_str}'",
                timestamp=timestamp_str,
            )
