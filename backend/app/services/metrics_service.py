"""
Metrics Service — Phase 6 Stub.

This service will collect and expose real-time service metrics:
- CPU and memory utilization per container
- Request rate, latency, and error rate
- Custom application metrics via Prometheus
- Time-series storage and querying

Implementation is deferred to Phase 6: Real-Time Observability.
"""
from __future__ import annotations


class MetricsService:
    """
    Collects, stores, and queries service metrics.

    Phase 6 will implement:
    - Prometheus scraping configuration
    - Metrics ingestion pipeline
    - Time-series database integration
    - Dashboard data API endpoints
    - Alerting thresholds
    """

    async def get_service_metrics(self, project_id: str, window_seconds: int = 60) -> dict:
        """
        Return recent metrics for a deployed service.

        Args:
            project_id: The CloudPilot project ID.
            window_seconds: Time window for metric aggregation.

        Returns:
            MetricsSnapshot with CPU, memory, request rate, etc.

        Raises:
            NotImplementedError: Until Phase 6 is implemented.
        """
        raise NotImplementedError("Metrics collection is implemented in Phase 6.")
