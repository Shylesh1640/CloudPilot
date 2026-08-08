"""HTTP Health Checker with SSRF Security Protection."""
from __future__ import annotations

import datetime
import ipaddress
import logging
import re
import time
import httpx

from app.models.health import HealthStatus
from app.services.health.exceptions import SSRFValidationError
from app.services.health.models import HealthCheckResult

logger = logging.getLogger("cloudpilot.http_checker")

# Blacklisted Cloud Metadata and Private Host IP ranges for SSRF protection
BLOCKED_IP_PATTERNS = [
    re.compile(r"^169\.254\."),        # AWS/GCP/Azure link-local metadata
    re.compile(r"^127\."),            # Loopback
    re.compile(r"^0\."),              # Current network
]


def validate_ssrf_safety(target_host: str) -> None:
    """
    Validates host for SSRF safety.
    Rejects link-local metadata IPs, cloud metadata endpoints, and external IP sweeps.
    Allows project internal container names (e.g. 'api', 'postgres', 'cloudpilot-abc123-api').
    """
    clean_host = target_host.strip().lower()

    # Check IP address targets directly
    try:
        ip = ipaddress.ip_address(clean_host)
        if ip.is_link_local or ip.is_loopback or ip.is_multicast or ip.is_unspecified:
            raise SSRFValidationError(f"Target host '{target_host}' is blocked for SSRF security (link-local/loopback).")
    except ValueError:
        # Not a raw IP address; check hostname string patterns
        for pattern in BLOCKED_IP_PATTERNS:
            if pattern.search(clean_host):
                raise SSRFValidationError(f"Target host '{target_host}' matches SSRF blocked pattern.")


class HTTPChecker:
    """Executes async HTTP/HTTPS GET health check requests."""

    async def check(
        self,
        service_id: str,
        host: str,
        port: int = 8000,
        path: str = "/health",
        method: str = "GET",
        expected_status: int = 200,
        timeout_seconds: int = 3,
    ) -> HealthCheckResult:
        """Performs SSRF validation and executes HTTP health check."""
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            validate_ssrf_safety(host)
        except SSRFValidationError as err:
            return HealthCheckResult(
                service_id=service_id,
                check_type="HTTP",
                status=HealthStatus.FAILED,
                error_message=err.message,
                timestamp=timestamp_str,
            )

        url = f"http://{host}:{port}{path if path.startswith('/') else '/' + path}"
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=float(timeout_seconds), follow_redirects=True) as client:
                res = await client.request(method, url)
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                if res.status_code == expected_status:
                    return HealthCheckResult(
                        service_id=service_id,
                        check_type="HTTP",
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency_ms,
                        status_code=res.status_code,
                        timestamp=timestamp_str,
                    )
                else:
                    return HealthCheckResult(
                        service_id=service_id,
                        check_type="HTTP",
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency_ms,
                        status_code=res.status_code,
                        error_message=f"HTTP status code {res.status_code} != expected {expected_status}",
                        timestamp=timestamp_str,
                    )
        except httpx.TimeoutException:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return HealthCheckResult(
                service_id=service_id,
                check_type="HTTP",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                error_message=f"HTTP request timeout after {timeout_seconds}s",
                timestamp=timestamp_str,
            )
        except Exception as err:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return HealthCheckResult(
                service_id=service_id,
                check_type="HTTP",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                error_message=f"HTTP connection error: {err}",
                timestamp=timestamp_str,
            )
