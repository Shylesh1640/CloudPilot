"""RepositoryAnalyzer orchestrator — executes detectors, updates progress, and builds normalized RepositoryProfile."""
from __future__ import annotations

import logging
from typing import Callable
from pathlib import Path

from app.services.repository_analyzer.detectors.cache_detector import CacheDetector
from app.services.repository_analyzer.detectors.database_detector import DatabaseDetector
from app.services.repository_analyzer.detectors.dependency_detector import DependencyDetector
from app.services.repository_analyzer.detectors.docker_detector import DockerDetector
from app.services.repository_analyzer.detectors.environment_detector import EnvironmentDetector
from app.services.repository_analyzer.detectors.framework_detector import FrameworkDetector
from app.services.repository_analyzer.detectors.language_detector import LanguageDetector
from app.services.repository_analyzer.detectors.port_detector import PortDetector
from app.services.repository_analyzer.detectors.queue_detector import QueueDetector
from app.services.repository_analyzer.detectors.service_detector import ServiceDetector
from app.services.repository_analyzer.limits import AnalysisLimits, DEFAULT_LIMITS
from app.services.repository_analyzer.models import (
    RepositoryInfo,
    RepositoryProfile,
)
from app.services.repository_analyzer.scanner import RepositoryScanner

logger = logging.getLogger("cloudpilot.analyzer")


class RepositoryAnalyzer:
    """Central orchestrator for static repository analysis."""

    def __init__(self, limits: AnalysisLimits = DEFAULT_LIMITS) -> None:
        self.limits = limits
        self.scanner = RepositoryScanner(limits)
        self.language_detector = LanguageDetector()
        self.framework_detector = FrameworkDetector()
        self.dependency_detector = DependencyDetector()
        self.database_detector = DatabaseDetector()
        self.cache_detector = CacheDetector()
        self.queue_detector = QueueDetector()
        self.docker_detector = DockerDetector()
        self.port_detector = PortDetector()
        self.environment_detector = EnvironmentDetector()
        self.service_detector = ServiceDetector()

    def analyze(
        self,
        repo_dir: str | Path,
        repo_url: str,
        owner: str,
        name: str,
        commit_sha: str | None = None,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> RepositoryProfile:
        """
        Analyze cloned repository files and return normalized RepositoryProfile.
        Updates progress via progress_callback if provided.
        """
        def update_progress(pct: int, status_msg: str) -> None:
            if progress_callback:
                progress_callback(pct, status_msg)

        logger.info(f"Starting analysis for {owner}/{name}")

        # 1. Scanning (25%)
        update_progress(25, "Scanning repository files")
        scan_result = self.scanner.scan(repo_dir)

        # 2. Language Detection (40%)
        update_progress(40, "Detecting programming languages")
        languages = self.language_detector.detect(scan_result)

        # 3. Dependency Detection (55%)
        update_progress(55, "Analyzing package dependencies")
        package_managers, dependencies = self.dependency_detector.detect(scan_result)

        # 4. Framework Detection (65%)
        update_progress(65, "Detecting web frameworks")
        frameworks = self.framework_detector.detect(scan_result)
        framework_names = [f.name for f in frameworks]

        # 5. Database, Cache, Queue Detection (75%)
        update_progress(75, "Detecting infrastructure & services")
        databases = self.database_detector.detect(scan_result, dependencies)
        db_names = [d.name for d in databases]

        caches = self.cache_detector.detect(scan_result, dependencies)
        queues = self.queue_detector.detect(scan_result, dependencies)

        # 6. Docker & Ports (85%)
        update_progress(85, "Analyzing container and port configuration")
        docker_info = self.docker_detector.detect(scan_result)
        ports = self.port_detector.detect(scan_result, docker_info, framework_names, db_names)

        # 7. Environment Variables (90%)
        update_progress(90, "Inspecting environment configuration")
        env_vars = self.environment_detector.detect(scan_result)

        # 8. Services & Monorepo Inference (95%)
        update_progress(95, "Inferring application architecture")
        services, is_monorepo, monorepo_apps = self.service_detector.detect(
            scan_result,
            docker_info,
            ports,
            framework_names,
            db_names,
            [c.name for c in caches],
            [q.name for q in queues],
        )

        # Extract README summary
        readme_summary = self._extract_readme_summary(scan_result)

        # 9. Finalizing Profile (100%)
        profile = RepositoryProfile(
            repository=RepositoryInfo(
                owner=owner,
                name=name,
                url=repo_url,
                commit_sha=commit_sha,
            ),
            languages=languages,
            package_managers=package_managers,
            frameworks=frameworks,
            dependencies=dependencies,
            databases=databases,
            caches=caches,
            queues=queues,
            containers=docker_info,
            ports=ports,
            environment_variables=env_vars,
            services=services,
            is_monorepo=is_monorepo,
            monorepo_apps=monorepo_apps,
            readme_summary=readme_summary,
        )

        update_progress(100, "Analysis completed")
        logger.info(f"Analysis completed successfully for {owner}/{name}")
        return profile

    def _extract_readme_summary(self, scan_result: ScanResult) -> str | None:
        readme_obj = (
            scan_result.priority_files.get("readme.md")
            or scan_result.priority_files.get("README.md")
        )
        if readme_obj:
            text = readme_obj.read_text(max_kb=50)
            if text:
                # Return first 500 characters of README text
                lines = [
                    line.strip()
                    for line in text.splitlines()
                    if line.strip() and not line.startswith("#")
                ]
                return " ".join(lines)[:500] if lines else None
        return None
