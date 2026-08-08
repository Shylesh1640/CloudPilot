"""DeploymentMetricsAggregator — aggregates service metrics across deployment."""
from __future__ import annotations

import datetime
import uuid
from app.services.observability.schemas import DeploymentMetricsRead, ServiceMetricsRead


class DeploymentMetricsAggregator:
    @staticmethod
    def aggregate(
        deployment_id: uuid.UUID,
        service_metrics: dict[str, ServiceMetricsRead],
    ) -> DeploymentMetricsRead:
        now = datetime.datetime.now(datetime.timezone.utc)
        if not service_metrics:
            return DeploymentMetricsRead(
                deployment_id=deployment_id,
                timestamp=now,
                total_cpu_percent=0.0,
                avg_cpu_percent=0.0,
                total_memory_usage_bytes=0,
                avg_memory_percent=0.0,
                total_network_rx_rate=0.0,
                total_network_tx_rate=0.0,
                total_restarts=0,
                services={},
            )

        services_list = list(service_metrics.values())
        total_cpu = round(sum(s.cpu_percent for s in services_list), 2)
        avg_cpu = round(total_cpu / len(services_list), 2)
        total_mem = sum(s.memory_usage_bytes for s in services_list)
        avg_mem = round(sum(s.memory_percent for s in services_list) / len(services_list), 2)
        total_rx = round(sum(s.network_rx_rate for s in services_list), 2)
        total_tx = round(sum(s.network_tx_rate for s in services_list), 2)
        total_restarts = sum(s.restart_count for s in services_list)

        return DeploymentMetricsRead(
            deployment_id=deployment_id,
            timestamp=now,
            total_cpu_percent=total_cpu,
            avg_cpu_percent=avg_cpu,
            total_memory_usage_bytes=total_mem,
            avg_memory_percent=avg_mem,
            total_network_rx_rate=total_rx,
            total_network_tx_rate=total_tx,
            total_restarts=total_restarts,
            services=service_metrics,
        )
