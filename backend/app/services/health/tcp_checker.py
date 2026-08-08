"""TCP Health Checker for non-HTTP infrastructure services (databases, caches)."""
from __future__ import annotations

import asyncio
import datetime
import logging
import time

from app.models.health import HealthStatus
from app.services.health.http_checker import validate_ssrf_safety
from app.services.health.models import HealthCheckResult

logger = logging.getLogger("cloudpilot.tcp_checker")


class TCPChecker:
    """Executes async TCP socket health checks."""

    async def check(
        self,
        service_id: str,
        host: str,
        port: int,
        timeout_seconds: int = 3,
    ) -> HealthCheckResult:
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            validate_ssrf_safety(host)
        except Exception as err:
            return HealthCheckResult(
                service_id=service_id,
                check_type="TCP",
                status=HealthStatus.FAILED,
                error_message=str(err),
                timestamp=timestamp_str,
            )

        start_time = time.perf_counter()
        try:
            conn = asyncio.open_connection(host, port)
            _reader, writer = await asyncio.wait_for(conn, timeout=float(timeout_seconds))
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            writer.close()
            await writer.wait_closed()

            return HealthCheckResult(
                service_id=service_id,
                check_type="TCP",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                status_code=200,
                timestamp=timestamp_str,
            )
        except asyncio.TimeoutError:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return HealthCheckResult(
                service_id=service_id,
                check_type="TCP",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                error_message=f"TCP connection timeout after {timeout_seconds}s",
                timestamp=timestamp_str,
            )
        except Exception as err:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return HealthCheckResult(
                service_id=service_id,
                check_type="TCP",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                error_message=f"TCP connection refused: {err}",
                timestamp=timestamp_str,
            )
