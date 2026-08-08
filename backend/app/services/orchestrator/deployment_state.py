"""DeploymentState — tracks desired vs actual container state and performs reconciliation."""
from __future__ import annotations

import logging
from typing import Any

from app.models.deployment import ServiceActualState, ServiceDesiredState
from app.services.orchestrator.docker_client import ContainerRuntime

logger = logging.getLogger("cloudpilot.deployment_state")


class DeploymentStateReconciler:
    def __init__(self, runtime: ContainerRuntime) -> None:
        self.runtime = runtime

    def inspect_actual_state(self, container_name_or_id: str) -> tuple[ServiceActualState, str]:
        """Inspects Docker runtime to get actual state."""
        info = self.runtime.inspect_container(container_name_or_id)
        state_dict = info.get("State", {})
        status_str = state_dict.get("Status", "unknown").lower()

        if status_str in ("running", "restarting"):
            return ServiceActualState.RUNNING, status_str
        elif status_str in ("exited", "dead"):
            return ServiceActualState.EXITED, status_str
        elif status_str in ("created",):
            return ServiceActualState.CREATED, status_str
        else:
            return ServiceActualState.UNKNOWN, status_str

    def reconcile_service(self, container_name_or_id: str, desired: ServiceDesiredState) -> dict[str, Any]:
        """
        Compares desired state vs actual runtime state.
        Returns dictionary indicating if drift was detected.
        """
        actual, raw_status = self.inspect_actual_state(container_name_or_id)
        drift = False

        if desired == ServiceDesiredState.RUNNING and actual != ServiceActualState.RUNNING:
            drift = True
            logger.warning(f"DRIFT DETECTED for '{container_name_or_id}': Desired=RUNNING, Actual={actual}")

        return {
            "container": container_name_or_id,
            "desired_state": desired,
            "actual_state": actual,
            "raw_status": raw_status,
            "drift_detected": drift,
        }
