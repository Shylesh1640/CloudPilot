"""Service and monorepo detector — infers component services and monorepo application layouts."""
from __future__ import annotations

from app.services.repository_analyzer.models import DockerInfo, PortInfo, ServiceInfo
from app.services.repository_analyzer.scanner import ScanResult

COMMON_SERVICE_DIRS = {
    "frontend": {"type": "application", "runtime": "node"},
    "client": {"type": "application", "runtime": "node"},
    "ui": {"type": "application", "runtime": "node"},
    "web": {"type": "application", "runtime": "node"},
    "backend": {"type": "application", "runtime": None},
    "api": {"type": "application", "runtime": None},
    "server": {"type": "application", "runtime": None},
    "worker": {"type": "worker", "runtime": None},
    "jobs": {"type": "worker", "runtime": None},
    "services": {"type": "application", "runtime": None},
}


class ServiceDetector:
    def detect(
        self,
        scan_result: ScanResult,
        docker_info: DockerInfo,
        ports: list[PortInfo],
        frameworks: list[str],
        databases: list[str],
        caches: list[str],
        queues: list[str],
    ) -> tuple[list[ServiceInfo], bool, list[str]]:
        """
        Returns (services_list, is_monorepo, monorepo_apps).
        """
        services: list[ServiceInfo] = []
        seen_service_names: set[str] = set()

        # Check for monorepo configuration indicators
        is_monorepo = False
        monorepo_apps: list[str] = []

        monorepo_configs = {"pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json"}
        for f in scan_result.files:
            fn = f.relative_path.split("/")[-1].lower()
            if fn in monorepo_configs:
                is_monorepo = True
                break

        # Discover top-level directories
        top_dirs = set()
        for f in scan_result.files:
            parts = f.relative_path.split("/")
            if len(parts) > 1:
                top_dirs.add(parts[0].lower())

        if "apps" in top_dirs or "packages" in top_dirs:
            is_monorepo = True

        if is_monorepo:
            # Look for app folders under apps/ or services/
            for f in scan_result.files:
                parts = f.relative_path.split("/")
                if len(parts) >= 2 and parts[0].lower() in ("apps", "packages", "services"):
                    app_name = parts[1]
                    if app_name not in monorepo_apps and not app_name.startswith("."):
                        monorepo_apps.append(app_name)

        # 1. Infer services from top-level directory names
        for dir_name in top_dirs:
            if dir_name in COMMON_SERVICE_DIRS:
                spec = COMMON_SERVICE_DIRS[dir_name]
                seen_service_names.add(dir_name)

                # Match port if available
                matched_port = None
                for p in ports:
                    if dir_name in p.service.lower() or p.service.lower() in dir_name:
                        matched_port = p.port
                        break

                services.append(
                    ServiceInfo(
                        name=dir_name,
                        type=spec["type"],
                        runtime=spec["runtime"],
                        port=matched_port,
                        confidence=0.85,
                        evidence=[f"Top-level directory '{dir_name}' detected"],
                    )
                )

        # 2. Add services from docker-compose services
        for compose_svc in docker_info.compose_services:
            if compose_svc.lower() not in seen_service_names:
                seen_service_names.add(compose_svc.lower())

                # Categorize docker compose service
                svc_lower = compose_svc.lower()
                if any(db.lower() in svc_lower for db in databases):
                    svc_type = "database"
                elif any(c.lower() in svc_lower for c in caches):
                    svc_type = "cache"
                elif any(q.lower() in svc_lower for q in queues) or "worker" in svc_lower:
                    svc_type = "worker"
                else:
                    svc_type = "application"

                matched_port = None
                for p in ports:
                    if svc_lower in p.service.lower():
                        matched_port = p.port
                        break

                services.append(
                    ServiceInfo(
                        name=compose_svc,
                        type=svc_type,
                        port=matched_port,
                        confidence=0.9,
                        evidence=[f"Docker Compose service '{compose_svc}'"],
                    )
                )

        # 3. If single root application with no distinct subdirectories found
        if not services:
            # Fallback to single primary application
            main_fw = frameworks[0] if frameworks else "Application"
            matched_port = ports[0].port if ports else None
            services.append(
                ServiceInfo(
                    name="api" if any(f in main_fw for f in ("FastAPI", "Express", "Flask", "Gin")) else "app",
                    type="application",
                    framework=main_fw,
                    port=matched_port,
                    confidence=0.75,
                    evidence=["Single-application repository structure"],
                )
            )

        # 4. Include explicit infrastructure services if detected but not in services list yet
        for db in databases:
            db_svc_name = db.lower()
            if not any(db_svc_name in s.name.lower() for s in services):
                services.append(
                    ServiceInfo(
                        name=db_svc_name,
                        type="database",
                        confidence=0.9,
                        evidence=[f"{db} database detected"],
                    )
                )

        return services, is_monorepo, monorepo_apps
