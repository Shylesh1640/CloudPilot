"""Custom exceptions for repository analysis."""
from __future__ import annotations


class RepositoryAnalysisError(Exception):
    """Base exception for all repository analysis errors."""
    code: str = "ANALYSIS_ERROR"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message


class InvalidGitHubURL(RepositoryAnalysisError):
    code = "INVALID_GITHUB_URL"


class RepositoryCloneFailed(RepositoryAnalysisError):
    code = "REPOSITORY_CLONE_FAILED"


class RepositoryTooLarge(RepositoryAnalysisError):
    code = "REPOSITORY_TOO_LARGE"


class AnalysisTimeout(RepositoryAnalysisError):
    code = "ANALYSIS_TIMEOUT"
