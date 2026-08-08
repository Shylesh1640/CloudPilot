"""Repository file scanner with size enforcement and directory filtering."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.repository_analyzer.exceptions import RepositoryTooLarge
from app.services.repository_analyzer.limits import AnalysisLimits, DEFAULT_LIMITS

# Directories to skip entirely during scan
IGNORED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    "target",
    "vendor",
    ".idea",
    ".vscode",
}

# Key configuration / manifest files to prioritize
PRIORITY_FILES = {
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "go.mod",
    "go.sum",
    "pom.xml",
    "build.gradle",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    ".env.example",
    ".env.sample",
    "README.md",
    "readme.md",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
    "next.config.mjs",
    "tsconfig.json",
    "turbo.json",
    "nx.json",
}


@dataclass
class ScannedFile:
    relative_path: str  # e.g. "backend/app/main.py"
    absolute_path: Path
    size_bytes: int
    is_priority: bool = False

    def read_text(self, max_kb: int = 2048) -> str | None:
        """Safely read text contents up to max_kb limit."""
        if self.size_bytes > max_kb * 1024:
            return None
        try:
            return self.absolute_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None


@dataclass
class ScanResult:
    root_path: Path
    files: list[ScannedFile] = field(default_factory=list)
    total_files: int = 0
    total_size_bytes: int = 0
    file_tree: dict[str, Any] = field(default_factory=dict)
    priority_files: dict[str, ScannedFile] = field(default_factory=dict)  # filename -> ScannedFile


class RepositoryScanner:
    def __init__(self, limits: AnalysisLimits = DEFAULT_LIMITS) -> None:
        self.limits = limits

    def scan(self, repo_dir: str | Path) -> ScanResult:
        root = Path(repo_dir).resolve()
        files: list[ScannedFile] = []
        priority_map: dict[str, ScannedFile] = {}
        total_size = 0

        for dirpath, dirnames, filenames in os.walk(root):
            # Mutate dirnames in-place to skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]

            current_dir = Path(dirpath)

            for filename in filenames:
                if filename.startswith(".git"):
                    continue

                abs_path = current_dir / filename
                rel_path = str(abs_path.relative_to(root)).replace("\\", "/")

                try:
                    file_size = abs_path.stat().st_size
                except OSError:
                    continue

                # Check total limits
                if len(files) >= self.limits.max_files:
                    raise RepositoryTooLarge(
                        f"Repository contains more than {self.limits.max_files:,} files.",
                        code="MAX_FILES_EXCEEDED",
                    )

                total_size += file_size
                if total_size > self.limits.max_repo_size_mb * 1024 * 1024:
                    raise RepositoryTooLarge(
                        f"Repository total size exceeds limit of {self.limits.max_repo_size_mb} MB.",
                        code="MAX_SIZE_EXCEEDED",
                    )

                is_prio = filename.lower() in {p.lower() for p in PRIORITY_FILES}
                scanned_file = ScannedFile(
                    relative_path=rel_path,
                    absolute_path=abs_path,
                    size_bytes=file_size,
                    is_priority=is_prio,
                )
                files.append(scanned_file)

                if is_prio:
                    # Keep path or name in priority map
                    priority_map[rel_path] = scanned_file
                    priority_map[filename.lower()] = scanned_file

        file_tree = self._build_file_tree(files)

        return ScanResult(
            root_path=root,
            files=files,
            total_files=len(files),
            total_size_bytes=total_size,
            file_tree=file_tree,
            priority_files=priority_map,
        )

    def _build_file_tree(self, files: list[ScannedFile], max_depth: int = 4) -> dict[str, Any]:
        """Build a simplified file tree dictionary (up to max_depth)."""
        tree: dict[str, Any] = {}
        for f in files:
            parts = f.relative_path.split("/")
            if len(parts) > max_depth:
                continue
            curr = tree
            for part in parts[:-1]:
                if part not in curr or not isinstance(curr[part], dict):
                    curr[part] = {}
                curr = curr[part]
            curr[parts[-1]] = None  # None indicates a file
        return tree
