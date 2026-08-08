"""Port detector — extracts application and database port assignments."""
from __future__ import annotations

import json
import re
from app.services.repository_analyzer.models import DockerInfo, PortInfo
from app.services.repository_analyzer.scanner import ScanResult

DEFAULT_FRAMEWORK_PORTS = [
    {"framework": "FastAPI", "port": 8000, "service": "api"},
    {"framework": "Django", "port": 8000, "service": "backend"},
    {"framework": "Flask", "port": 5000, "service": "backend"},
    {"framework": "React", "port": 5173, "service": "frontend"},
    {"framework": "Next.js", "port": 3000, "service": "frontend"},
    {"framework": "Express", "port": 3000, "service": "api"},
    {"framework": "NestJS", "port": 3000, "service": "api"},
    {"framework": "Spring Boot", "port": 8080, "service": "backend"},
    {"framework": "Gin", "port": 8080, "service": "backend"},
]

DEFAULT_DATABASE_PORTS = [
    {"db": "PostgreSQL", "port": 5432, "service": "postgresql"},
    {"db": "MySQL", "port": 3306, "service": "mysql"},
    {"db": "MongoDB", "port": 27017, "service": "mongodb"},
    {"db": "Redis", "port": 6379, "service": "redis"},
]


class PortDetector:
    def detect(
        self,
        scan_result: ScanResult,
        docker_info: DockerInfo,
        frameworks: list[str],
        databases: list[str],
    ) -> list[PortInfo]:
        ports: list[PortInfo] = []
        seen_ports: set[int] = set()

        # 1. Exposed ports from Dockerfile
        for p in docker_info.exposed_ports:
            if p not in seen_ports:
                seen_ports.add(p)
                ports.append(
                    PortInfo(
                        port=p,
                        service="application",
                        port_type="application_port",
                        source="Dockerfile EXPOSE",
                    )
                )

        # 2. Ports in docker-compose.yml (e.g. "8000:8000")
        compose_obj = (
            scan_result.priority_files.get("docker-compose.yml")
            or scan_result.priority_files.get("compose.yml")
        )
        if compose_obj:
            text = compose_obj.read_text()
            if text:
                mappings = re.findall(r'["\']?(\d+):(\d+)["\']?', text)
                for host_p, container_p in mappings:
                    p = int(container_p)
                    if p not in seen_ports:
                        seen_ports.add(p)
                        ports.append(
                            PortInfo(
                                port=p,
                                service="service",
                                port_type="service_port",
                                source=f"docker-compose.yml ({host_p}:{container_p})",
                            )
                        )

        # 3. Ports in package.json scripts (e.g. vite --port 5173)
        pkg_json = scan_result.priority_files.get("package.json")
        if pkg_json:
            text = pkg_json.read_text()
            if text:
                try:
                    data = json.loads(text)
                    scripts = " ".join(data.get("scripts", {}).values())
                    port_matches = re.findall(r"--port\s+(\d+)", scripts)
                    for p_str in port_matches:
                        p = int(p_str)
                        if p not in seen_ports:
                            seen_ports.add(p)
                            ports.append(
                                PortInfo(
                                    port=p,
                                    service="frontend",
                                    port_type="application_port",
                                    source="package.json script --port",
                                )
                            )
                except json.JSONDecodeError:
                    pass

        # 4. Fallback ports based on detected frameworks
        for fw_name in frameworks:
            for item in DEFAULT_FRAMEWORK_PORTS:
                if item["framework"].lower() == fw_name.lower():
                    p = item["port"]
                    if p not in seen_ports:
                        seen_ports.add(p)
                        ports.append(
                            PortInfo(
                                port=p,
                                service=item["service"],
                                port_type="application_port",
                                source=f"{fw_name} default port",
                            )
                        )

        # 5. Database ports
        for db_name in databases:
            for item in DEFAULT_DATABASE_PORTS:
                if item["db"].lower() == db_name.lower():
                    p = item["port"]
                    if p not in seen_ports:
                        seen_ports.add(p)
                        ports.append(
                            PortInfo(
                                port=p,
                                service=item["service"],
                                port_type="service_port",
                                source=f"{db_name} default port",
                            )
                        )

        return ports
