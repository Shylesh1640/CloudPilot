"""Observability Engine custom exceptions."""
from __future__ import annotations


class ObservabilityError(Exception):
    code: str = "OBSERVABILITY_ERROR"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message


class MetricsCollectionError(ObservabilityError):
    code = "METRICS_COLLECTION_ERROR"


class WebSocketAuthError(ObservabilityError):
    code = "WEBSOCKET_AUTH_ERROR"
