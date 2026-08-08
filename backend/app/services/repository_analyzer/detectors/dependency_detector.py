"""Dependency detector — extracts dependency lists and package manager types."""
from __future__ import annotations

import json
import re
from app.services.repository_analyzer.scanner import ScanResult


class DependencyDetector:
    def detect(self, scan_result: ScanResult) -> tuple[list[str], dict[str, list[str]]]:
        """
        Returns (package_managers, dependencies_dict).
        package_managers: list of detected package managers e.g. ["npm", "pip"]
        dependencies_dict: {"npm": [...], "pip": [...]}
        """
        package_managers: list[str] = []
        dependencies: dict[str, list[str]] = {}

        for f in scan_result.files:
            filename = f.relative_path.split("/")[-1]

            # npm / yarn / pnpm
            if filename == "package.json":
                if "npm" not in package_managers:
                    package_managers.append("npm")
                content = f.read_text()
                if content:
                    try:
                        data = json.loads(content)
                        pkgs = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
                        dependencies.setdefault("npm", []).extend(pkgs)
                    except json.JSONDecodeError:
                        pass

            elif filename == "yarn.lock" and "yarn" not in package_managers:
                package_managers.append("yarn")
            elif filename == "pnpm-lock.yaml" and "pnpm" not in package_managers:
                package_managers.append("pnpm")

            # pip / poetry / pipenv
            elif filename == "requirements.txt":
                if "pip" not in package_managers:
                    package_managers.append("pip")
                content = f.read_text()
                if content:
                    pkgs = [
                        line.strip().split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
                        for line in content.splitlines()
                        if line.strip() and not line.startswith("#") and not line.startswith("-")
                    ]
                    dependencies.setdefault("pip", []).extend(pkgs)

            elif filename == "pyproject.toml":
                if "poetry" not in package_managers and "poetry" in (f.read_text() or ""):
                    package_managers.append("poetry")

            elif filename == "Pipfile":
                if "pipenv" not in package_managers:
                    package_managers.append("pipenv")

            # Go
            elif filename == "go.mod":
                if "go modules" not in package_managers:
                    package_managers.append("go modules")
                content = f.read_text()
                if content:
                    pkgs = re.findall(r"\t([^\s]+)", content)
                    dependencies.setdefault("go modules", []).extend(pkgs)

            # Java
            elif filename == "pom.xml":
                if "maven" not in package_managers:
                    package_managers.append("maven")
                content = f.read_text()
                if content:
                    pkgs = re.findall(r"<artifactId>([^<]+)</artifactId>", content)
                    dependencies.setdefault("maven", []).extend(pkgs)

            elif filename in ("build.gradle", "build.gradle.kts"):
                if "gradle" not in package_managers:
                    package_managers.append("gradle")

        # Deduplicate
        for mgr in dependencies:
            dependencies[mgr] = list(dict.fromkeys(dependencies[mgr]))

        return package_managers, dependencies
