"""
Autoscaler Service — Phase 7 Stub.

This service will automatically scale running services based on metrics:
- Scale up when CPU/memory exceeds thresholds
- Scale down when load decreases
- Respect min/max replica bounds
- Integrate with traffic generation for load testing

Implementation is deferred to Phase 7: Autoscaling.
"""
from __future__ import annotations


class Autoscaler:
    """
    Automatically scales services based on observed metrics.

    Phase 7 will implement:
    - Horizontal pod/container scaling decisions
    - Cooldown period management
    - Scale-up and scale-down policies
    - Integration with MetricsService
    - Load test integration (k6 or Locust)
    """

    async def evaluate(self, project_id: str) -> dict:
        """
        Evaluate scaling decisions for a running project.

        Args:
            project_id: The CloudPilot project ID.

        Returns:
            ScalingDecision with recommended replica count and rationale.

        Raises:
            NotImplementedError: Until Phase 7 is implemented.
        """
        raise NotImplementedError("Autoscaling is implemented in Phase 7.")

    async def scale(self, project_id: str, replicas: int) -> None:
        """
        Apply a scaling action to a running service.

        Raises:
            NotImplementedError: Until Phase 7 is implemented.
        """
        raise NotImplementedError("Autoscaling is implemented in Phase 7.")
