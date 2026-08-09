"""
Phase 11 — README Auto-Generation Service.

Takes a completed repository analysis profile and uses the configured AI
provider to generate a production-quality README.md with deployment
instructions, environment variable documentation, and architecture overview.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.project_repository import ProjectRepository
from app.services.ai.provider import get_ai_provider
from app.services.ai.exceptions import AIProviderError

logger = logging.getLogger("cloudpilot.readme_service")

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are an expert technical writer and DevOps engineer.
Your task is to generate a high-quality, production-ready README.md for a software project
based on a structured repository profile.

RULES:
- Output ONLY the raw markdown content, no JSON, no preamble, no explanation.
- Use standard GitHub-flavoured Markdown.
- Include: Project title, badges, overview, features, tech stack, prerequisites,
  installation, environment variables table, running locally, Docker/deployment section,
  API endpoints (if detectable), project structure, and contributing guide.
- Be specific — use the actual framework/database/tool names from the profile.
- Do NOT hallucinate features that are not in the profile.
- For environment variables, create a markdown table with columns: Variable | Required | Description.
- Keep it concise but complete. Aim for ~200-400 lines."""

_USER_PROMPT_TEMPLATE = """Generate a complete README.md for the following repository.

Repository Profile:
---
Owner: {owner}
Name: {name}
URL: {url}

Primary Language: {primary_language}
Frameworks: {frameworks}
Databases: {databases}
Has Dockerfile: {has_dockerfile}
Has Docker Compose: {has_compose}
Compose Services: {compose_services}
Exposed Ports: {ports}
Package Managers: {package_managers}

README Summary (from actual repo):
{readme_summary}

Environment Variables:
{env_vars}

Detected Services:
{services}
---

Generate the full README.md now. Output only markdown."""


def _build_prompt(profile: dict) -> str:
    """Build the user prompt from the analysis profile dict."""
    repo = profile.get("repository", {})
    langs = profile.get("languages", {})
    frameworks = [f.get("name", "") for f in profile.get("frameworks", []) if isinstance(f, dict)]
    databases = [d.get("name", "") for d in profile.get("databases", []) if isinstance(d, dict)]
    containers = profile.get("containers", {})
    ports = [str(p.get("port", "")) for p in profile.get("ports", []) if isinstance(p, dict)]
    env_vars = profile.get("environment_variables", [])
    services = profile.get("services", [])
    package_managers = profile.get("package_managers", [])

    # Format env vars table input
    env_lines = []
    for ev in env_vars:
        if isinstance(ev, dict):
            name = ev.get("name", "")
            sensitive = ev.get("sensitive", False)
            source = ev.get("source", "")
            env_lines.append(f"  - {name} (sensitive={sensitive}, source={source})")
    env_block = "\n".join(env_lines) if env_lines else "  None detected"

    # Format services
    svc_lines = []
    for svc in services:
        if isinstance(svc, dict):
            svc_lines.append(f"  - {svc.get('name','?')} (type={svc.get('type','?')})")
    svc_block = "\n".join(svc_lines) if svc_lines else "  None detected"

    return _USER_PROMPT_TEMPLATE.format(
        owner=repo.get("owner", ""),
        name=repo.get("name", ""),
        url=repo.get("url", ""),
        primary_language=langs.get("primary", "Unknown"),
        frameworks=", ".join(frameworks) or "None detected",
        databases=", ".join(databases) or "None detected",
        has_dockerfile=containers.get("has_dockerfile", False),
        has_compose=containers.get("has_compose", False),
        compose_services=", ".join(containers.get("compose_services", [])) or "None",
        ports=", ".join(ports) or "None detected",
        package_managers=", ".join(package_managers) if isinstance(package_managers, list) else str(package_managers),
        readme_summary=profile.get("readme_summary", "Not available")[:800],
        env_vars=env_block,
        services=svc_block,
    )


class ReadmeGenerationError(Exception):
    pass


class ReadmeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._analysis_repo = AnalysisRepository(session)
        self._project_repo = ProjectRepository(session)

    async def generate(
        self,
        *,
        analysis_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        """
        Generate a README.md string for the given completed analysis.
        Returns the raw markdown string.
        """
        analysis = await self._analysis_repo.get(analysis_id)
        if not analysis:
            raise ReadmeGenerationError("Analysis not found.")

        # Ownership check
        project = await self._project_repo.get_by_id_for_user(analysis.project_id, user_id)
        if not project:
            raise ReadmeGenerationError("Access denied.")

        if analysis.status.value != "COMPLETED":
            raise ReadmeGenerationError(
                f"Analysis is not completed (status={analysis.status.value}). "
                "Run and complete analysis first."
            )

        profile = analysis.analysis_result
        if not profile:
            raise ReadmeGenerationError("Analysis result is empty.")

        prompt = _build_prompt(profile)

        try:
            provider = get_ai_provider()
            logger.info(
                "Generating README for analysis=%s using provider=%s",
                analysis_id,
                provider.__class__.__name__,
            )
            raw = await provider.generate_text(prompt, _SYSTEM_PROMPT)
            return raw.strip()
        except AIProviderError as err:
            logger.error("AI provider error during README generation: %s", err)
            raise ReadmeGenerationError(str(err))
        except Exception as exc:
            logger.exception("Unexpected error generating README: %s", exc)
            raise ReadmeGenerationError("An unexpected error occurred generating the README.")
