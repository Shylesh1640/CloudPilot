"""Exceptions for Deployment & Health Check Engine."""
from __future__ import annotations


class HealthCheckError(Exception):
    """Base exception for health check errors."""
    code: str = "HEALTH_CHECK_ERROR"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message


class SSRFValidationError(HealthCheckError):
    code = "SSRF_VALIDATION_ERROR"


class HealthTimeoutError(HealthCheckError):
    code = "HEALTH_TIMEOUT"
