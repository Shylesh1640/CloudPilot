"""AI Provider abstraction layer for OpenAI, Gemini, OpenRouter, and Deterministic Mock."""
from __future__ import annotations

import abc
import json
import logging
from typing import Any
import httpx

from app.core.config import settings
from app.services.ai.exceptions import AIProviderError

logger = logging.getLogger("cloudpilot.ai_provider")


class BaseAIProvider(abc.ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str = settings.AI_MODEL, api_key: str = settings.AI_API_KEY) -> None:
        self.model = model
        self.api_key = api_key

    @abc.abstractmethod
    async def generate_json(self, prompt: str, system_prompt: str) -> str:
        """Send prompt to LLM and return raw JSON response string."""
        pass

    async def generate_text(self, prompt: str, system_prompt: str) -> str:
        """Send prompt to LLM and return raw text response (markdown, prose, etc.).
        Default implementation calls generate_json and strips any JSON wrapping.
        Providers should override this for cleaner text responses.
        """
        return await self.generate_json(prompt, system_prompt)


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider implementation."""

    async def _call(self, prompt: str, system_prompt: str, json_mode: bool = False) -> str:
        if not self.api_key:
            raise AIProviderError("OpenAI API key is not configured.")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "model": self.model or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    raise AIProviderError(f"OpenAI API error ({res.status_code}): {res.text}")
                return res.json()["choices"][0]["message"]["content"]
            except AIProviderError:
                raise
            except Exception as err:
                raise AIProviderError(f"Failed to communicate with OpenAI: {err}")

    async def generate_json(self, prompt: str, system_prompt: str) -> str:
        return await self._call(prompt, system_prompt, json_mode=True)

    async def generate_text(self, prompt: str, system_prompt: str) -> str:
        return await self._call(prompt, system_prompt, json_mode=False)


class GeminiProvider(BaseAIProvider):
    """Google Gemini REST API provider implementation."""

    async def _call(self, prompt: str, system_prompt: str, json_mode: bool = False) -> str:
        if not self.api_key:
            raise AIProviderError("Gemini API key is not configured.")
        model = self.model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        mime = "application/json" if json_mode else "text/plain"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": mime, "temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    raise AIProviderError(f"Gemini API error ({res.status_code}): {res.text}")
                return res.json()["candidates"][0]["content"]["parts"][0]["text"]
            except AIProviderError:
                raise
            except Exception as err:
                raise AIProviderError(f"Failed to communicate with Gemini: {err}")

    async def generate_json(self, prompt: str, system_prompt: str) -> str:
        return await self._call(prompt, system_prompt, json_mode=True)

    async def generate_text(self, prompt: str, system_prompt: str) -> str:
        return await self._call(prompt, system_prompt, json_mode=False)


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter API provider implementation (OpenAI-compatible)."""

    async def _call(self, prompt: str, system_prompt: str, json_mode: bool = False) -> str:
        if not self.api_key:
            raise AIProviderError("OpenRouter API key is not configured.")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cloudpilot.dev",
            "X-Title": "CloudPilot",
        }
        payload: dict[str, Any] = {
            "model": self.model or "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    raise AIProviderError(f"OpenRouter API error ({res.status_code}): {res.text}")
                return res.json()["choices"][0]["message"]["content"]
            except AIProviderError:
                raise
            except Exception as err:
                raise AIProviderError(f"Failed to communicate with OpenRouter: {err}")

    async def generate_json(self, prompt: str, system_prompt: str) -> str:
        return await self._call(prompt, system_prompt, json_mode=True)

    async def generate_text(self, prompt: str, system_prompt: str) -> str:
        return await self._call(prompt, system_prompt, json_mode=False)


class DeterministicFallbackProvider(BaseAIProvider):
    """
    Deterministic Mock Provider — converts RepositoryProfile context into a safe,
    evidence-matched InfrastructurePlan JSON without needing external LLM API calls.
    Used for local dev and automated tests.
    """

    async def generate_json(self, prompt: str, system_prompt: str) -> str:
        # Extract profile from prompt if JSON embedded
        try:
            profile_data = json.loads(prompt)
        except Exception:
            profile_data = {}

        repo_name = profile_data.get("repository", {}).get("name", "app")
        frameworks = [f.get("name") for f in profile_data.get("frameworks", []) if isinstance(f, dict)]
        databases = [d.get("name") for d in profile_data.get("databases", []) if isinstance(d, dict)]
        caches = [c.get("name") for c in profile_data.get("caches", []) if isinstance(c, dict)]
        queues = [q.get("name") for q in profile_data.get("queues", []) if isinstance(q, dict)]
        services_raw = profile_data.get("services", [])
        ports_raw = profile_data.get("ports", [])
        env_raw = profile_data.get("environment_variables", [])

        # Build services
        services: list[dict[str, Any]] = []
        dependencies: list[dict[str, Any]] = []
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        volumes: list[dict[str, Any]] = []
        env_list: list[dict[str, Any]] = []
        health_checks: list[dict[str, Any]] = []
        resource_profiles: list[dict[str, Any]] = []
        scaling: list[dict[str, Any]] = []
        deployment_order: list[str] = []

        # Application services
        app_services = [s for s in services_raw if isinstance(s, dict) and s.get("type") in ("application", "worker")]
        if not app_services:
            app_services = [{"name": "api", "type": "application", "runtime": "python", "framework": frameworks[0] if frameworks else "FastAPI"}]

        # Databases
        db_services = []
        for db_name in databases:
            db_id = db_name.lower().replace(" ", "")
            db_services.append({"id": db_id, "name": db_name, "type": "database", "port": 5432 if "postg" in db_id else 3306})
            volumes.append({"name": f"{db_id}-data", "service": db_id, "persistent": True, "mount_path": "/var/lib/" + db_id})
            deployment_order.append(db_id)

        # Caches
        cache_services = []
        for cache_name in caches:
            cache_id = cache_name.lower().replace(" ", "")
            cache_services.append({"id": cache_id, "name": cache_name, "type": "cache", "port": 6379})
            deployment_order.append(cache_id)

        # Process App Services
        for idx, app_svc in enumerate(app_services):
            svc_name = app_svc.get("name", f"app-{idx+1}").lower()
            svc_type = app_svc.get("type", "application")
            is_public = (idx == 0 and svc_type == "application")  # Primary web app is public
            matched_port = app_svc.get("port") or (5173 if "react" in svc_name or "front" in svc_name else 8000)

            svc_def = {
                "id": svc_name,
                "name": svc_name.capitalize(),
                "type": svc_type,
                "runtime": app_svc.get("runtime"),
                "framework": app_svc.get("framework") or (frameworks[0] if frameworks else None),
                "source_path": f"/{svc_name}",
                "port": matched_port if is_public or svc_type == "application" else None,
                "protocol": "http",
                "public": is_public,
                "replicas": {"min": 1, "max": 5 if svc_type == "application" else 3, "initial": 1},
                "scalable": True,
                "confidence": 0.9,
                "evidence": [f"Detected {svc_type} service '{svc_name}'"],
            }
            services.append(svc_def)
            deployment_order.append(svc_name)

            nodes.append({
                "id": svc_name,
                "label": svc_name.capitalize(),
                "type": svc_type,
                "runtime": app_svc.get("runtime"),
                "framework": app_svc.get("framework"),
                "public": is_public,
                "replicas": 1,
            })

            # Dependencies from app -> db / cache
            for db in db_services:
                dependencies.append({"source": svc_name, "target": db["id"], "dependency_type": "database", "required": True})
                edges.append({"source": svc_name, "target": db["id"], "label": "queries", "dependency_type": "database"})
            for c in cache_services:
                dependencies.append({"source": svc_name, "target": c["id"], "dependency_type": "cache", "required": False})
                edges.append({"source": svc_name, "target": c["id"], "label": "caches", "dependency_type": "cache"})

            health_checks.append({
                "service": svc_name,
                "type": "http",
                "path": "/health",
                "port": matched_port,
                "interval_seconds": 10,
                "timeout_seconds": 3,
                "failure_threshold": 3,
            })

            resource_profiles.append({
                "service": svc_name,
                "cpu": "0.5",
                "memory": "512Mi",
                "confidence": 0.8,
                "reason": "Standard baseline allocation for application runtime",
            })

            scaling.append({
                "service": svc_name,
                "metric": "cpu",
                "scale_up_threshold": 75,
                "scale_down_threshold": 30,
                "cooldown_seconds": 60,
            })

            # Environment variables
            env_vars_list = []
            for ev in env_raw:
                if isinstance(ev, dict):
                    env_vars_list.append({
                        "name": ev.get("name", "VAR"),
                        "source": "environment",
                        "secret": ev.get("sensitive", False),
                        "required": True,
                        "default": None,
                    })
            if env_vars_list:
                env_list.append({"service": svc_name, "variables": env_vars_list})

        # Add DB nodes
        for db in db_services:
            services.append({
                "id": db["id"],
                "name": db["name"],
                "type": "database",
                "port": db["port"],
                "public": False,
                "replicas": {"min": 1, "max": 1, "initial": 1},
                "scalable": False,
                "confidence": 0.95,
                "evidence": [f"{db['name']} database detected"],
            })
            nodes.append({"id": db["id"], "label": db["name"], "type": "database", "public": False, "replicas": 1})

        # Add Cache nodes
        for c in cache_services:
            services.append({
                "id": c["id"],
                "name": c["name"],
                "type": "cache",
                "port": c["port"],
                "public": False,
                "replicas": {"min": 1, "max": 1, "initial": 1},
                "scalable": False,
                "confidence": 0.95,
                "evidence": [f"{c['name']} cache detected"],
            })
            nodes.append({"id": c["id"], "label": c["name"], "type": "cache", "public": False, "replicas": 1})

        plan = {
            "plan_version": "1.0",
            "analyzer_version": "2.0",
            "planner_version": "1.0",
            "application": {
                "name": repo_name,
                "architecture_type": "multi_service" if len(services) > 1 else "single_service",
            },
            "services": services,
            "networks": [{"name": "cloudpilot-internal", "type": "private"}],
            "volumes": volumes,
            "dependencies": dependencies,
            "environment": env_list,
            "scaling": scaling,
            "health_checks": health_checks,
            "resource_profiles": resource_profiles,
            "risks": [
                {
                    "risk": "single_database_instance",
                    "severity": "medium",
                    "description": "Database runs as a single persistent instance; failover requires manual intervention.",
                    "mitigation": "Enable automated storage backups and health monitoring.",
                }
            ],
            "graph": {"nodes": nodes, "edges": edges},
            "explanation": {
                "summary": f"Generated infrastructure topology for {repo_name} containing {len(services)} services.",
                "architecture_choice": "Multi-service topology with internal private networking.",
                "scaling_reasoning": "Application tier is stateless and configured for horizontal autoscaling based on CPU utilization.",
                "security_notes": "Database and cache instances are kept strictly private to the internal network.",
            },
            "deployment_order": deployment_order,
        }

        return json.dumps(plan)


def get_ai_provider() -> BaseAIProvider:
    """Factory function returning configured AI provider instance."""
    provider_name = settings.AI_PROVIDER.lower()
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "openrouter":
        return OpenRouterProvider()
    else:
        return DeterministicFallbackProvider()
