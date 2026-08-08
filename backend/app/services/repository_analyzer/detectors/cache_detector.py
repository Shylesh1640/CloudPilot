"""Cache detector — identifies Redis, Valkey, Memcached from dependencies, compose, and env vars."""
from __future__ import annotations

import re
from app.services.repository_analyzer.models import DetectionItem
from app.services.repository_analyzer.scanner import ScanResult

CACHE_RULES = [
    {
        "name": "Redis",
        "packages": ["redis", "ioredis", "aioredis", "django-redis", "go-redis"],
        "env_patterns": [r"REDIS_URL", r"REDIS_HOST"],
        "compose_images": ["redis"],
    },
    {
        "name": "Valkey",
        "packages": ["valkey"],
        "env_patterns": [r"VALKEY"],
        "compose_images": ["valkey"],
    },
    {
        "name": "Memcached",
        "packages": ["memcached", "pymemcache", "aiomemcached"],
        "env_patterns": [r"MEMCACHED"],
        "compose_images": ["memcached"],
    },
]


class CacheDetector:
    def detect(self, scan_result: ScanResult, dependencies: dict[str, list[str]]) -> list[DetectionItem]:
        detected: list[DetectionItem] = []
        all_deps = [dep.lower() for deps in dependencies.values() for dep in deps]

        env_text = "\n".join(
            f.read_text() or ""
            for f in scan_result.files
            if f.relative_path.endswith((".env.example", ".env.sample", ".env"))
        )
        compose_text = "\n".join(
            f.read_text() or ""
            for f in scan_result.files
            if f.relative_path.split("/")[-1].lower() in ("docker-compose.yml", "compose.yml")
        )

        for rule in CACHE_RULES:
            name = rule["name"]
            evidence: list[str] = []
            score = 0.0

            for pkg in rule["packages"]:
                if any(pkg in dep for dep in all_deps):
                    evidence.append(f"Dependency '{pkg}' detected")
                    score += 0.5

            for pat in rule["env_patterns"]:
                if re.search(pat, env_text, re.IGNORECASE):
                    evidence.append(f"Environment pattern '{pat}' matched")
                    score += 0.3

            for img in rule["compose_images"]:
                if re.search(rf"image:\s*.*{img}", compose_text, re.IGNORECASE):
                    evidence.append(f"Docker Compose service image '{img}'")
                    score += 0.5

            if score > 0 and evidence:
                detected.append(
                    DetectionItem(
                        name=name,
                        confidence=min(round(score, 2), 0.99),
                        evidence=list(dict.fromkeys(evidence)),
                    )
                )

        return detected
