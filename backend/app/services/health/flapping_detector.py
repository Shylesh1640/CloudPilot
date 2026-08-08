"""FlappingDetector — detects services rapidly oscillating between HEALTHY and UNHEALTHY."""
from __future__ import annotations

import datetime
from collections import defaultdict
from app.models.health import HealthStatus
from app.services.health.policies import HealthPolicy


class FlappingDetector:
    def __init__(self, policy: HealthPolicy | None = None) -> None:
        self.policy = policy or HealthPolicy()
        # History: service_id -> list of (timestamp, status_str)
        self._history: dict[str, list[tuple[datetime.datetime, HealthStatus]]] = defaultdict(list)

    def record_and_check_flapping(self, service_id: str, new_status: HealthStatus) -> bool:
        """
        Records health check result and checks if service is flapping.
        Returns True if flapping is detected.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(seconds=self.policy.flapping_window_seconds)

        history = self._history[service_id]
        # Append new state
        history.append((now, new_status))
        # Clean older history entries
        self._history[service_id] = [h for h in history if h[0] >= cutoff]

        # Count state switches in active window
        recent = self._history[service_id]
        switches = 0
        for i in range(1, len(recent)):
            if recent[i][1] != recent[i - 1][1]:
                switches += 1

        is_flapping = switches >= self.policy.flapping_threshold_switches
        return is_flapping
