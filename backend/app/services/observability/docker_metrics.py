"""DockerMetricsProvider — collects and normalizes Docker stats nanoseconds into CPU %, memory %, and network rates."""
from __future__ import annotations

import datetime
import logging
from typing import Any

from app.services.observability.models import NormalizedContainerMetrics
from app.services.orchestrator import ContainerRuntime, DockerRuntime

logger = logging.getLogger("cloudpilot.docker_metrics")


def calculate_cpu_percent(stats: dict[str, Any]) -> float:
    """Calculates normalized CPU usage percentage across available CPU cores."""
    try:
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})

        cpu_total = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        precpu_total = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)

        sys_cpu = cpu_stats.get("system_cpu_usage", 0)
        presys_cpu = precpu_stats.get("system_cpu_usage", 0)

        cpu_delta = float(cpu_total - precpu_total)
        sys_delta = float(sys_cpu - presys_cpu)

        if sys_delta > 0.0 and cpu_delta > 0.0:
            online_cpus = cpu_stats.get("online_cpus")
            if not online_cpus:
                percpu = cpu_stats.get("cpu_usage", {}).get("percpu_usage") or []
                online_cpus = len(percpu) if percpu else 1
            return round((cpu_delta / sys_delta) * float(online_cpus) * 100.0, 2)
    except Exception as exc:
        logger.debug(f"Error calculating CPU percent: {exc}")

    return 0.0


def calculate_memory_metrics(stats: dict[str, Any]) -> tuple[int, int | None, float]:
    """Extracts memory usage bytes, memory limit bytes, and calculates memory percent."""
    try:
        mem_stats = stats.get("memory_stats", {})
        usage = mem_stats.get("usage", 0)
        # Subtract cache bytes if available for accurate RSS
        stats_sub = mem_stats.get("stats", {})
        cache = stats_sub.get("inactive_file", 0) or stats_sub.get("cache", 0)
        rss_usage = max(0, usage - cache)

        limit = mem_stats.get("limit")
        if limit and limit > 1000000000000:  # If default unlimited host limit
            limit = None

        percent = round((float(rss_usage) / float(limit)) * 100.0, 2) if limit else 0.0
        return rss_usage, limit, percent
    except Exception as exc:
        logger.debug(f"Error calculating memory metrics: {exc}")

    return 0, None, 0.0


def calculate_network_bytes(stats: dict[str, Any]) -> tuple[int, int]:
    """Aggregates total network RX and TX bytes across all interfaces."""
    rx = 0
    tx = 0
    try:
        networks = stats.get("networks", {})
        for _iface, net_data in networks.items():
            rx += net_data.get("rx_bytes", 0)
            tx += net_data.get("tx_bytes", 0)
    except Exception as exc:
        logger.debug(f"Error calculating network bytes: {exc}")

    return rx, tx


def calculate_block_io_bytes(stats: dict[str, Any]) -> tuple[int | None, int | None]:
    """Extracts block read and write bytes where available."""
    read_bytes = 0
    write_bytes = 0
    has_data = False
    try:
        blkio = stats.get("blkio_stats", {}).get("io_service_bytes_recursive") or []
        for entry in blkio:
            op = entry.get("op", "").lower()
            val = entry.get("value", 0)
            if op == "read":
                read_bytes += val
                has_data = True
            elif op == "write":
                write_bytes += val
                has_data = True
    except Exception:
        pass

    return (read_bytes, write_bytes) if has_data else (None, None)


class DockerMetricsProvider:
    def __init__(self, runtime: ContainerRuntime | None = None) -> None:
        self.runtime = runtime or DockerRuntime()
        self._prev_net_cache: dict[str, tuple[datetime.datetime, int, int]] = {}

    def collect_container_telemetry(
        self,
        project_id: str,
        deployment_id: str,
        service_id: str,
        container_name_or_id: str,
    ) -> NormalizedContainerMetrics | None:
        """Fetches raw Docker stats and transforms into NormalizedContainerMetrics."""
        inspect_info = self.runtime.inspect_container(container_name_or_id)
        state_dict = inspect_info.get("State", {})
        running = state_dict.get("Running", False)
        container_state = state_dict.get("Status", "unknown").lower()
        restart_count = state_dict.get("RestartCount", 0)

        if not running:
            return NormalizedContainerMetrics(
                project_id=project_id,
                deployment_id=deployment_id,
                service_id=service_id,
                container_id=container_name_or_id,
                cpu_percent=0.0,
                memory_usage_bytes=0,
                memory_percent=0.0,
                network_rx_bytes=0,
                network_tx_bytes=0,
                network_rx_rate=0.0,
                network_tx_rate=0.0,
                restart_count=restart_count,
                container_state=container_state,
            )

        # Raw Docker stats API
        stats = self.runtime.get_container_stats(container_name_or_id)
        if not stats:
            return None

        now = datetime.datetime.now(datetime.timezone.utc)
        cpu_percent = calculate_cpu_percent(stats)
        mem_usage, mem_limit, mem_percent = calculate_memory_metrics(stats)
        rx_bytes, tx_bytes = calculate_network_bytes(stats)
        blk_read, blk_write = calculate_block_io_bytes(stats)

        # Calculate network rate (bytes/sec) based on previous sample cache
        rx_rate = 0.0
        tx_rate = 0.0
        if container_name_or_id in self._prev_net_cache:
            prev_time, prev_rx, prev_tx = self._prev_net_cache[container_name_or_id]
            dt = (now - prev_time).total_seconds()
            if dt > 0:
                rx_rate = round(max(0.0, float(rx_bytes - prev_rx) / dt), 2)
                tx_rate = round(max(0.0, float(tx_bytes - prev_tx) / dt), 2)

        self._prev_net_cache[container_name_or_id] = (now, rx_bytes, tx_bytes)

        return NormalizedContainerMetrics(
            project_id=project_id,
            deployment_id=deployment_id,
            service_id=service_id,
            container_id=container_name_or_id,
            timestamp=now,
            cpu_percent=cpu_percent,
            memory_usage_bytes=mem_usage,
            memory_limit_bytes=mem_limit,
            memory_percent=mem_percent,
            network_rx_bytes=rx_bytes,
            network_tx_bytes=tx_bytes,
            network_rx_rate=rx_rate,
            network_tx_rate=tx_rate,
            block_read_bytes=blk_read,
            block_write_bytes=blk_write,
            restart_count=restart_count,
            container_state=container_state,
        )
