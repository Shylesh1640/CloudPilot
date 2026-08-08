"""Git operations wrapper for shallow cloning public GitHub repositories."""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from typing import Generator
from contextlib import contextmanager

from app.services.repository_analyzer.exceptions import InvalidGitHubURL, RepositoryCloneFailed
from app.services.repository_analyzer.limits import AnalysisLimits, DEFAULT_LIMITS

logger = logging.getLogger("cloudpilot.git")

GITHUB_URL_REGEX = re.compile(
    r"^https://github\.com/(?P<owner>[a-zA-Z0-9_.-]+)/(?P<repo>[a-zA-Z0-9_.-]+?)(?:\.git)?$"
)


def parse_github_url(url: str) -> tuple[str, str]:
    """Parse and validate a public GitHub repository URL into (owner, repo_name)."""
    cleaned_url = url.strip().rstrip("/")
    match = GITHUB_URL_REGEX.match(cleaned_url)
    if not match:
        raise InvalidGitHubURL(
            "Invalid public GitHub URL format. Example: https://github.com/owner/repository",
            code="INVALID_GITHUB_URL",
        )
    owner = match.group("owner")
    repo = match.group("repo")
    return owner, repo


@contextmanager
def clone_repository(
    url: str,
    limits: AnalysisLimits = DEFAULT_LIMITS,
) -> Generator[tuple[str, str], None, None]:
    """
    Shallow clone a public GitHub repository to a temporary directory.
    Yields (temp_dir_path, commit_sha). Automatically deletes temporary files on context exit.
    """
    owner, repo_name = parse_github_url(url)
    target_url = f"https://github.com/{owner}/{repo_name}.git"
    temp_dir = tempfile.mkdtemp(prefix=f"cloudpilot_scan_{repo_name}_")

    try:
        logger.info(f"Cloning repository {target_url} to {temp_dir}")
        result = subprocess.run(
            [
                "git", "clone",
                "--depth", "1",
                "--single-branch",
                target_url,
                temp_dir,
            ],
            capture_output=True,
            text=True,
            timeout=limits.clone_timeout_seconds,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip() if result.stderr else "Unknown git error"
            logger.error(f"Git clone failed for {target_url}: {stderr}")
            raise RepositoryCloneFailed(
                f"Failed to clone repository from GitHub. Ensure the repository exists and is public.",
                code="REPOSITORY_CLONE_FAILED",
            )

        # Get the commit SHA
        sha_result = subprocess.run(
            ["git", "-C", temp_dir, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        commit_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else "unknown"

        yield temp_dir, commit_sha

    except subprocess.TimeoutExpired:
        logger.error(f"Git clone timed out after {limits.clone_timeout_seconds}s for {target_url}")
        raise RepositoryCloneFailed(
            f"Cloning repository timed out (> {limits.clone_timeout_seconds}s). Repository may be too large.",
            code="REPOSITORY_CLONE_TIMEOUT",
        )
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"Removed temporary clone directory {temp_dir}")
