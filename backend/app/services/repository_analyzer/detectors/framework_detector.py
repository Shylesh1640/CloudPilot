"""Framework detector — inspects package manifests and source files for framework signatures."""
from __future__ import annotations

import json
import re
from typing import Any

from app.services.repository_analyzer.models import DetectionItem
from app.services.repository_analyzer.scanner import ScanResult

FRAMEWORK_SIGNATURES: list[dict[str, Any]] = [
    # Python
    {
        "name": "FastAPI",
        "category": "Python",
        "packages": ["fastapi"],
        "files": ["main.py", "app.py"],
        "import_keywords": ["import fastapi", "from fastapi import"],
    },
    {
        "name": "Flask",
        "category": "Python",
        "packages": ["flask"],
        "files": ["app.py", "wsgi.py"],
        "import_keywords": ["import flask", "from flask import"],
    },
    {
        "name": "Django",
        "category": "Python",
        "packages": ["django"],
        "files": ["manage.py", "settings.py", "wsgi.py", "asgi.py"],
        "import_keywords": ["import django", "from django."],
    },
    # JavaScript / TypeScript
    {
        "name": "Next.js",
        "category": "JavaScript",
        "packages": ["next"],
        "files": ["next.config.js", "next.config.mjs", "next.config.ts"],
        "import_keywords": ["from 'next'", 'from "next"'],
    },
    {
        "name": "React",
        "category": "JavaScript",
        "packages": ["react", "react-dom"],
        "files": ["App.tsx", "App.jsx", "index.tsx", "index.jsx"],
        "import_keywords": ["from 'react'", 'from "react"'],
    },
    {
        "name": "Express",
        "category": "JavaScript",
        "packages": ["express"],
        "files": ["app.js", "index.js", "server.js", "app.ts"],
        "import_keywords": ["require('express')", 'require("express")', "from 'express'"],
    },
    {
        "name": "NestJS",
        "category": "JavaScript",
        "packages": ["@nestjs/core"],
        "files": ["nest-cli.json", "main.ts"],
        "import_keywords": ["@nestjs/core"],
    },
    # Go
    {
        "name": "Gin",
        "category": "Go",
        "packages": ["github.com/gin-gonic/gin"],
        "import_keywords": ["github.com/gin-gonic/gin"],
    },
    {
        "name": "Echo",
        "category": "Go",
        "packages": ["github.com/labstack/echo"],
        "import_keywords": ["github.com/labstack/echo"],
    },
    # Java
    {
        "name": "Spring Boot",
        "category": "Java",
        "packages": ["spring-boot-starter-web", "org.springframework.boot"],
        "files": ["application.properties", "application.yml"],
        "import_keywords": ["org.springframework.boot"],
    },
]


class FrameworkDetector:
    def detect(self, scan_result: ScanResult) -> list[DetectionItem]:
        detected: list[DetectionItem] = []

        # Gather package dependencies from manifests
        manifest_deps = self._extract_all_manifest_dependencies(scan_result)

        for sig in FRAMEWORK_SIGNATURES:
            evidence: list[str] = []
            score = 0.0
            fw_name = sig["name"]

            # Check manifest package matches
            for pkg in sig.get("packages", []):
                for manifest_file, deps in manifest_deps.items():
                    if any(pkg.lower() in d.lower() for d in deps):
                        evidence.append(f"{manifest_file} contains {pkg}")
                        score += 0.6

            # Check characteristic file existence
            for f in scan_result.files:
                filename = f.relative_path.split("/")[-1]
                if filename in sig.get("files", []):
                    evidence.append(f"File {f.relative_path} detected")
                    score += 0.2

            # Check import statements in key source files
            for f in scan_result.files:
                if f.relative_path.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java")):
                    text = f.read_text(max_kb=100)
                    if text:
                        for kw in sig.get("import_keywords", []):
                            if kw in text:
                                evidence.append(f"{f.relative_path} imports {fw_name}")
                                score += 0.2
                                break  # 1 hit per file is enough

            if score > 0 and evidence:
                confidence = min(round(score, 2), 0.99)
                detected.append(
                    DetectionItem(
                        name=fw_name,
                        confidence=confidence,
                        evidence=list(dict.fromkeys(evidence)),  # deduplicate
                    )
                )

        return detected

    def _extract_all_manifest_dependencies(self, scan_result: ScanResult) -> dict[str, list[str]]:
        deps_by_file: dict[str, list[str]] = {}

        for f in scan_result.files:
            rel = f.relative_path
            filename = rel.split("/")[-1].lower()

            # Node package.json
            if filename == "package.json":
                content = f.read_text()
                if content:
                    try:
                        data = json.loads(content)
                        all_deps = list(data.get("dependencies", {}).keys()) + list(
                            data.get("devDependencies", {}).keys()
                        )
                        deps_by_file[rel] = all_deps
                    except json.JSONDecodeError:
                        pass

            # Python requirements.txt
            elif filename == "requirements.txt":
                content = f.read_text()
                if content:
                    lines = [
                        line.strip().split("==")[0].split(">=")[0].split("<=")[0].strip()
                        for line in content.splitlines()
                        if line.strip() and not line.startswith("#")
                    ]
                    deps_by_file[rel] = lines

            # Python pyproject.toml
            elif filename == "pyproject.toml":
                content = f.read_text()
                if content:
                    # Simple regex matching for dependencies
                    found = re.findall(r'([a-zA-Z0-9_-]+)\s*=\s*["\']', content)
                    deps_by_file[rel] = found

            # Go go.mod
            elif filename == "go.mod":
                content = f.read_text()
                if content:
                    found = re.findall(r"\t([^\s]+)", content)
                    deps_by_file[rel] = found

            # Java pom.xml / build.gradle
            elif filename in ("pom.xml", "build.gradle"):
                content = f.read_text()
                if content:
                    deps_by_file[rel] = [content]  # Keep full text for regex match

        return deps_by_file
