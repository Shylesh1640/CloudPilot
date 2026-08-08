"""System prompt and prompt builder for AI Architecture Planner."""
from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are CloudPilot's AI Infrastructure Architecture Planner.

Your task is to convert an evidence-backed repository profile into a production-oriented, machine-readable infrastructure plan JSON.

You MUST follow these strict rules:
1. Return ONLY valid JSON matching the required schema. No markdown formatting outside JSON.
2. Identify all application services, database services, cache services, and queue services.
3. Establish explicit service dependency relationships.
4. Determine internal and external ports. Preserving detected ports from Phase 2.
5. NEVER mark databases, caches, or queue services as publicly accessible (`public` MUST be false for database/cache/queue).
6. NEVER make databases horizontally scalable (`scalable` MUST be false, `max_replicas` MUST be 1 for database/cache).
7. Determine which services require persistent storage volumes.
8. Recommend initial resource limits (CPU, RAM) and health check endpoints.
9. Identify environment variable requirements without including actual secret values.
10. Return an architecture graph (nodes and edges) and clear AI explanations.
"""


def build_user_prompt(repository_profile: dict[str, Any]) -> str:
    """
    Sanitize repository profile and format structured JSON user prompt.
    Strips any sensitive credentials and retains technology metadata.
    """
    # Sanitize profile dictionary
    sanitized: dict[str, Any] = {
        "repository": repository_profile.get("repository", {}),
        "languages": repository_profile.get("languages", {}),
        "package_managers": repository_profile.get("package_managers", []),
        "frameworks": repository_profile.get("frameworks", []),
        "dependencies": repository_profile.get("dependencies", {}),
        "databases": repository_profile.get("databases", []),
        "caches": repository_profile.get("caches", []),
        "queues": repository_profile.get("queues", []),
        "containers": repository_profile.get("containers", {}),
        "ports": repository_profile.get("ports", []),
        "environment_variables": [
            {
                "name": env.get("name") if isinstance(env, dict) else str(env),
                "sensitive": env.get("sensitive", False) if isinstance(env, dict) else False,
            }
            for env in repository_profile.get("environment_variables", [])
        ],
        "services": repository_profile.get("services", []),
        "is_monorepo": repository_profile.get("is_monorepo", False),
        "monorepo_apps": repository_profile.get("monorepo_apps", []),
    }

    return json.dumps(sanitized, indent=2)
