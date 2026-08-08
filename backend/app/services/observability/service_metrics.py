"""ServiceMetricsAggregator — aggregates container metrics into service-level metrics."""
from __future__ import annotations

import datetime
from app.services.observability.models import NormalizedContainerMetrics
from app.services.observability.schemas import ServiceMetricsRead


class ServiceMetricsAggregator:
    @staticmethod
    def aggregate(
        service_id: str,
        container_metrics_list: list[NormalizedContainerMetrics],
    ) -> ServiceMetricsRead:
        now = datetime.datetime.now(datetime.timezone.utc)
        if not container_metrics_list:
            return ServiceMetricsRead(
                service_id=service_id,
                timestamp=now,
                cpu_percent=0.0,
                memory_usage_bytes=0,
                memory_limit_bytes=None,
                memory_percent=0.0,
                network_rx_rate=0.0,
                network_tx_rate=0.0,
                restart_count=0,
                container_state="unknown",
            )

        total_cpu = sum(m.cpu_percent for m in container_metrics_list)
        avg_cpu = round(total_cpu / len(container_metrics_list), 2)

        total_mem = sum(m.memory_usage_bytes for m in container_metrics_list)
        avg_mem_pct = round(sum(m.memory_percent for m in container_metrics_list) / len(container_metrics_list), 2)
        total_rx_rate = round(sum(m.network_rx_rate for m in container_metrics_list), 2)
        total_tx_rate = round(sum(m.network_tx_rate for m in container_metrics_list), 2)
        total_restarts = sum(m.restart_count for m in container_metrics_list)
        primary_state = container_metrics_list[0].container_state

        return ServiceMetricsRead(
            service_id=service_id,
            timestamp=now,
            cpu_percent=avg_cpu,
            memory_usage_bytes=total_mem,
            memory_limit_bytes=container_metrics_list[0].memory_limit_bytes,
            memory_percent=avg_mem_pct,
            network_rx_rate=total_rx_rate,
            network_tx_rate=total_tx_rate,
            restart_count=total_restarts,
            container_state=primary_state,
        )
