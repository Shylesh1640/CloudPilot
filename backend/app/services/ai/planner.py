"""AIArchitecturePlanner orchestrator — manages prompt formatting, LLM generation, validation retries, and fallback."""
from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import settings
from app.services.ai.exceptions import AIProviderError, MaxRetriesExceeded
from app.services.ai.prompts.architecture_planner import SYSTEM_PROMPT, build_user_prompt
from app.services.ai.provider import DeterministicFallbackProvider, get_ai_provider
from app.services.ai.schemas import InfrastructurePlan
from app.services.ai.validator import PlanValidator

logger = logging.getLogger("cloudpilot.ai_planner")


class AIArchitecturePlanner:
    """Central orchestrator for AI-driven infrastructure plan generation."""

    def __init__(self) -> None:
        self.validator = PlanValidator()
        self.provider = get_ai_provider()

    async def plan_architecture(
        self,
        repository_profile: dict[str, Any],
        max_retries: int = settings.AI_MAX_RETRIES,
    ) -> tuple[InfrastructurePlan, dict[str, Any], int]:
        """
        Generate and validate infrastructure plan from a RepositoryProfile.

        Returns: (validated_infrastructure_plan, validation_result_dict, duration_ms)
        """
        start_time = time.perf_counter()
        user_prompt = build_user_prompt(repository_profile)
        current_prompt = user_prompt
        validation_history: list[dict[str, Any]] = []

        for attempt in range(max_retries + 1):
            logger.info(f"AI Plan generation attempt {attempt + 1}/{max_retries + 1} (provider={settings.AI_PROVIDER})")
            try:
                raw_json = await self.provider.generate_json(current_prompt, SYSTEM_PROMPT)
                is_valid, plan, errors = self.validator.validate(raw_json)

                validation_history.append({
                    "attempt": attempt + 1,
                    "valid": is_valid,
                    "errors": errors,
                })

                if is_valid and plan is not None:
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    logger.info(f"AI Architecture Plan successfully generated and validated in {duration_ms}ms")
                    return plan, {"passed": True, "attempts": attempt + 1, "history": validation_history}, duration_ms

                logger.warning(f"Validation failed on attempt {attempt + 1}: {errors}")

                # Format correction prompt for retry
                current_prompt = (
                    f"{user_prompt}\n\n"
                    f"Your previous JSON response had validation errors:\n"
                    + "\n".join(f"- {e}" for e in errors)
                    + "\n\nPlease fix these errors and return valid JSON."
                )

            except AIProviderError as err:
                logger.warning(f"AI Provider error on attempt {attempt + 1}: {err}")
                if attempt == max_retries:
                    break

        # If LLM retries exhausted or provider unavailable, fallback to deterministic generator
        logger.info("Falling back to DeterministicFallbackProvider for guaranteed valid plan generation")
        fallback_provider = DeterministicFallbackProvider()
        fallback_json = await fallback_provider.generate_json(user_prompt, SYSTEM_PROMPT)
        is_valid, plan, errors = self.validator.validate(fallback_json)

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        validation_res = {
            "passed": is_valid,
            "fallback_used": True,
            "attempts": max_retries + 1,
            "history": validation_history,
            "errors": errors if not is_valid else [],
        }

        if not is_valid or plan is None:
            raise MaxRetriesExceeded("Failed to generate a valid infrastructure plan even after fallback.")

        return plan, validation_res, duration_ms
