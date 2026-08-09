from __future__ import annotations

import abc
import asyncio
import json

from app.core.config import settings
from app.services.ai.provider import get_ai_provider
from app.services.ai_incident.models import AIAnalysisStatus
from app.services.ai_incident.prompt_builder import SYSTEM_PROMPT


class IncidentAIProvider(abc.ABC):
    @abc.abstractmethod
    async def analyze_incident(self, prompt: str) -> tuple[AIAnalysisStatus, dict | None, str | None]:
        pass


class ConfiguredIncidentProvider(IncidentAIProvider):
    async def analyze_incident(self, prompt: str) -> tuple[AIAnalysisStatus, dict | None, str | None]:
        provider = get_ai_provider()
        if settings.AI_PROVIDER.lower() == "mock" or not settings.AI_API_KEY:
            return AIAnalysisStatus.AI_UNAVAILABLE, None, "No external incident AI provider is configured."
        for attempt in range(settings.AI_INCIDENT_MAX_RETRIES):
            try:
                raw = await asyncio.wait_for(provider.generate_json(prompt, SYSTEM_PROMPT), timeout=settings.AI_INCIDENT_TIMEOUT_SECONDS)
                return AIAnalysisStatus.AI_AVAILABLE, json.loads(raw), None
            except asyncio.TimeoutError:
                if attempt + 1 == settings.AI_INCIDENT_MAX_RETRIES:
                    return AIAnalysisStatus.AI_TIMEOUT, None, "Incident AI request timed out."
            except (ValueError, json.JSONDecodeError):
                return AIAnalysisStatus.AI_INVALID_RESPONSE, None, "Incident AI returned invalid JSON."
            except Exception as exc:
                if attempt + 1 == settings.AI_INCIDENT_MAX_RETRIES:
                    return AIAnalysisStatus.AI_UNAVAILABLE, None, str(exc)
        return AIAnalysisStatus.AI_UNAVAILABLE, None, "Incident AI provider unavailable."
