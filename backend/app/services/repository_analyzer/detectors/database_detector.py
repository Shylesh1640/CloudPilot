"""Database detector — checks dependencies, compose services, env vars, and code for database usage."""
from __future__ import annotations

import re
from app.services.repository_analyzer.models import DatabaseDetection
from app.services.repository_analyzer.scanner import ScanResult

DB_RULES: list[dict] = [
    {
        "name": "PostgreSQL",
        "packages": ["psycopg2", "psycopg", "asyncpg", "pg", "postgres", "jpa-postgresql"],
        "env_patterns": [r"POSTGRES", r"PGDATABASE", r"PGHOST", r"DATABASE_URL.*postgres"],
        "compose_images": ["postgres"],
        "port_default": 5432,
    },
    {
        "name": "MySQL",
        "packages": ["mysqlclient", "pymysql", "mysql2", "mysql"],
        "env_patterns": [r"MYSQL"],
        "compose_images": ["mysql"],
        "port_default": 3306,
    },
    {
        "name": "MariaDB",
        "packages": ["mariadb"],
        "env_patterns": [r"MARIADB"],
        "compose_images": ["mariadb"],
        "port_default": 3306,
    },
    {
        "name": "MongoDB",
        "packages": ["pymongo", "motor", "mongoose", "mongodb"],
        "env_patterns": [r"MONGO", r"MONGODB_URI"],
        "compose_images": ["mongo"],
        "port_default": 27017,
    },
    {
        "name": "SQLite",
        "packages": ["aiosqlite", "sqlite3"],
        "env_patterns": [r"SQLITE"],
        "compose_images": [],
        "port_default": None,
    },
]


class DatabaseDetector:
    def detect(self, scan_result: ScanResult, dependencies: dict[str, list[str]]) -> list[DatabaseDetection]:
        detected: list[DatabaseDetection] = []
        all_deps = [dep.lower() for deps in dependencies.values() for dep in deps]

        # Read env files text
        env_text = self._gather_env_text(scan_result)
        compose_text = self._gather_compose_text(scan_result)

        for rule in DB_RULES:
            db_name = rule["name"]
            evidence: list[str] = []
            score = 0.0

            # 1. Package dependencies
            for pkg in rule["packages"]:
                if any(pkg in dep for dep in all_deps):
                    evidence.append(f"Dependency package matching '{pkg}'")
                    score += 0.5

            # 2. Environment variables
            for pattern in rule["env_patterns"]:
                if re.search(pattern, env_text, re.IGNORECASE):
                    evidence.append(f"Environment variable matching '{pattern}'")
                    score += 0.3

            # 3. Docker compose image
            for img in rule["compose_images"]:
                if re.search(rf"image:\s*.*{img}", compose_text, re.IGNORECASE):
                    evidence.append(f"Docker Compose service using image '{img}'")
                    score += 0.5

            if score > 0 and evidence:
                confidence = min(round(score, 2), 0.99)
                if confidence >= 0.7:
                    certainty = "Detected"
                elif confidence >= 0.4:
                    certainty = "Likely"
                else:
                    certainty = "Possible"

                detected.append(
                    DatabaseDetection(
                        name=db_name,
                        confidence=confidence,
                        certainty=certainty,
                        evidence=list(dict.fromkeys(evidence)),
                    )
                )

        return detected

    def _gather_env_text(self, scan_result: ScanResult) -> str:
        text_parts = []
        for f in scan_result.files:
            if f.relative_path.endswith((".env.example", ".env.sample", ".env")):
                t = f.read_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts)

    def _gather_compose_text(self, scan_result: ScanResult) -> str:
        text_parts = []
        for f in scan_result.files:
            fn = f.relative_path.split("/")[-1].lower()
            if fn in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
                t = f.read_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts)
