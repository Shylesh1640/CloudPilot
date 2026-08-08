"""Queue & Messaging detector — identifies Celery, RabbitMQ, Kafka, NATS, BullMQ, RQ."""
from __future__ import annotations

import re
from app.services.repository_analyzer.models import DetectionItem
from app.services.repository_analyzer.scanner import ScanResult

QUEUE_RULES = [
    {
        "name": "Celery",
        "packages": ["celery"],
        "env_patterns": [r"CELERY_BROKER", r"CELERY_RESULT_BACKEND"],
        "compose_images": [],
    },
    {
        "name": "RabbitMQ",
        "packages": ["pika", "amqp", "amqplib"],
        "env_patterns": [r"RABBITMQ", r"AMQP_URL"],
        "compose_images": ["rabbitmq"],
    },
    {
        "name": "Kafka",
        "packages": ["kafka-python", "confluent-kafka", "kafkajs"],
        "env_patterns": [r"KAFKA_BROKERS", r"KAFKA_BOOTSTRAP_SERVERS"],
        "compose_images": ["kafka", "zookeeper"],
    },
    {
        "name": "BullMQ",
        "packages": ["bullmq", "bull"],
        "env_patterns": [],
        "compose_images": [],
    },
    {
        "name": "RQ",
        "packages": ["rq"],
        "env_patterns": [r"RQ_REDIS_URL"],
        "compose_images": [],
    },
    {
        "name": "NATS",
        "packages": ["nats-py", "nats.ws", "nats"],
        "env_patterns": [r"NATS_URL"],
        "compose_images": ["nats"],
    },
]


class QueueDetector:
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

        for rule in QUEUE_RULES:
            name = rule["name"]
            evidence: list[str] = []
            score = 0.0

            for pkg in rule["packages"]:
                if any(pkg in dep for dep in all_deps):
                    evidence.append(f"Dependency package '{pkg}' detected")
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
