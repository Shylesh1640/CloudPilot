"""Unit tests for HTTP, TCP, Container health checkers and SSRF protection."""
from __future__ import annotations

import pytest
from app.models.health import HealthStatus
from app.services.health.exceptions import SSRFValidationError
from app.services.health.http_checker import HTTPChecker, validate_ssrf_safety
from app.services.health.tcp_checker import TCPChecker


def test_ssrf_validation_allowed_hostnames():
    # Standard container aliases & DNS names should pass
    validate_ssrf_safety("api")
    validate_ssrf_safety("postgres")
    validate_ssrf_safety("redis")
    validate_ssrf_safety("cloudpilot-app-net")


def test_ssrf_validation_blocked_metadata_ips():
    # Cloud metadata endpoints and link-local addresses must be blocked
    with pytest.raises(SSRFValidationError):
        validate_ssrf_safety("169.254.169.254")

    with pytest.raises(SSRFValidationError):
        validate_ssrf_safety("169.254.170.2")

    with pytest.raises(SSRFValidationError):
        validate_ssrf_safety("127.0.0.1")


@pytest.mark.asyncio
async def test_http_checker_ssrf_blocked():
    checker = HTTPChecker()
    res = await checker.check(service_id="api", host="169.254.169.254", port=8000)
    assert res.status == HealthStatus.FAILED
    assert "blocked" in res.error_message.lower()


@pytest.mark.asyncio
async def test_tcp_checker_connection_refused():
    checker = TCPChecker()
    # Connect to invalid port on localhost (should refuse connection cleanly)
    res = await checker.check(service_id="redis", host="127.0.0.1", port=59999, timeout_seconds=1)
    # SSRF check blocks 127.0.0.1
    assert res.status == HealthStatus.FAILED
