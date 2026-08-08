"""Docker detector — statically parses Dockerfile and docker-compose.yml text files."""
from __future__ import annotations

import re
from app.services.repository_analyzer.models import DockerInfo
from app.services.repository_analyzer.scanner import ScanResult


class DockerDetector:
    def detect(self, scan_result: ScanResult) -> DockerInfo:
        info = DockerInfo()

        # Check Dockerfile
        dockerfile_obj = scan_result.priority_files.get("dockerfile")
        if dockerfile_obj:
            info.has_dockerfile = True
            info.detected = True
            text = dockerfile_obj.read_text()
            if text:
                self._parse_dockerfile_text(text, info)

        # Check Compose
        compose_obj = (
            scan_result.priority_files.get("docker-compose.yml")
            or scan_result.priority_files.get("docker-compose.yaml")
            or scan_result.priority_files.get("compose.yml")
            or scan_result.priority_files.get("compose.yaml")
        )
        if compose_obj:
            info.has_compose = True
            info.detected = True
            text = compose_obj.read_text()
            if text:
                self._parse_compose_text(text, info)

        return info

    def _parse_dockerfile_text(self, text: str, info: DockerInfo) -> None:
        for line in text.splitlines():
            line_str = line.strip()
            if line_str.startswith("#") or not line_str:
                continue

            # FROM image
            if line_str.upper().startswith("FROM "):
                parts = line_str.split()
                if len(parts) >= 2:
                    info.base_image = parts[1]

            # EXPOSE port
            elif line_str.upper().startswith("EXPOSE "):
                ports = re.findall(r"\d+", line_str)
                for p in ports:
                    try:
                        info.exposed_ports.append(int(p))
                    except ValueError:
                        pass

            # WORKDIR
            elif line_str.upper().startswith("WORKDIR "):
                parts = line_str.split()
                if len(parts) >= 2:
                    info.workdir = parts[1]

        info.exposed_ports = list(dict.fromkeys(info.exposed_ports))

    def _parse_compose_text(self, text: str, info: DockerInfo) -> None:
        # Simple indentation-based YAML service extractor
        in_services = False
        services: list[str] = []

        for line in text.splitlines():
            if line.strip().startswith("#"):
                continue
            if re.match(r"^services\s*:", line):
                in_services = True
                continue
            if in_services:
                # Key at 2 spaces depth is a service name e.g. "  backend:"
                match = re.match(r"^  ([a-zA-Z0-9_-]+)\s*:", line)
                if match:
                    services.append(match.group(1))
                elif line and not line.startswith(" "):
                    in_services = False

        info.compose_services = services
