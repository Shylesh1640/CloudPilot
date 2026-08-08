"""Unit tests for AIArchitecturePlanner using profile fixtures."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from app.services.ai import AIArchitecturePlanner

PROFILES_DIR = Path(__file__).parent / "fixtures" / "profiles"


@pytest.mark.asyncio
async def test_ai_planner_fastapi_react_profile():
    profile_path = PROFILES_DIR / "react_fastapi.json"
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    planner = AIArchitecturePlanner()
    plan, validation_res, duration_ms = await planner.plan_architecture(profile)

    assert plan is not None
    assert plan.application.name == "fastapi-react"
    assert len(plan.services) >= 2
    assert plan.explanation.summary != ""
    assert duration_ms >= 0
    assert validation_res["passed"] is True

    # Verify Database safety
    for svc in plan.services:
        if svc.type in ("database", "cache"):
            assert svc.public is False
            assert svc.scalable is False
            assert svc.replicas.max == 1

    # Verify Public Frontend / API port
    public_services = [s for s in plan.services if s.public]
    assert len(public_services) >= 1
