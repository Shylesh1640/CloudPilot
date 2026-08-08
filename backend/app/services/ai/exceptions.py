"""Custom exception classes for AI Infrastructure Architecture Planner."""
from __future__ import annotations


class AIPlannerError(Exception):
    """Base exception for all AI planning errors."""
    code: str = "AI_PLANNER_ERROR"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message


class AIProviderError(AIPlannerError):
    code = "AI_PROVIDER_ERROR"


class PlanValidationError(AIPlannerError):
    code = "PLAN_VALIDATION_ERROR"


class MaxRetriesExceeded(AIPlannerError):
    code = "MAX_RETRIES_EXCEEDED"
