"""
Structured logging configuration.

Provides a consistent log format across all application layers.
The middleware attaches request context (method, path, status, duration).
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


def configure_logging() -> None:
    """Configure root logger with a consistent format."""
    level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    # Suppress noisy libraries in non-debug mode
    if not settings.ENVIRONMENT == "development":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs each HTTP request with method, path, status code, and duration.

    Example output:
        2026-08-08T12:30:42Z INFO     GET /api/v1/projects → 200 (42ms)
    """

    def __init__(self, app, logger: logging.Logger | None = None) -> None:
        super().__init__(app)
        self._logger = logger or get_logger("cloudpilot.http")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            self._logger.error(
                "%s %s → 500 (%dms) — unhandled exception: %s",
                request.method,
                request.url.path,
                elapsed_ms,
                str(exc),
            )
            raise
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        self._logger.info(
            "%s %s → %d (%dms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
