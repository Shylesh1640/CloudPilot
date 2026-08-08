"""Integration tests for infrastructure planning API endpoints."""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trigger_plan_uncompleted_analysis(client: AsyncClient, auth_headers: dict[str, str]):
    # Random UUID
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/repository-analyses/{fake_id}/plan",
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_trigger_and_fetch_infrastructure_plan(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "test-proj-plan-api"},
        headers=auth_headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Trigger analysis
    anal_resp = await client.post(
        f"/api/v1/projects/{project_id}/repositories/analyze",
        json={"repository_url": "https://github.com/example/fastapi-react"},
        headers=auth_headers,
    )
    assert anal_resp.status_code == 202
    analysis_id = anal_resp.json()["id"]

    # Manually populate mock completed analysis result in test DB to trigger plan
    # (Since background tasks run asynchronously)
    from tests.conftest import TestSessionLocal
    from app.repositories.analysis_repository import AnalysisRepository

    mock_result = {
        "repository": {"owner": "example", "name": "fastapi-react", "url": "https://github.com/example/fastapi-react"},
        "languages": {"primary": "Python", "distribution": {"Python": 100.0}},
        "frameworks": [{"name": "FastAPI", "confidence": 0.98, "evidence": ["requirements.txt"]}],
        "dependencies": {"pip": ["fastapi", "uvicorn", "asyncpg"]},
        "databases": [{"name": "PostgreSQL", "confidence": 0.9, "certainty": "Detected", "evidence": ["asyncpg"]}],
        "caches": [],
        "queues": [],
        "containers": {"detected": True, "has_dockerfile": True, "has_compose": False, "exposed_ports": [8000]},
        "ports": [{"port": 8000, "service": "api", "port_type": "application_port", "source": "Dockerfile"}],
        "environment_variables": [],
        "services": [{"name": "api", "type": "application", "runtime": "python", "port": 8000}],
        "is_monorepo": False,
        "monorepo_apps": [],
    }

    async with TestSessionLocal() as session:
        repo = AnalysisRepository(session)
        await repo.save_result(uuid.UUID(analysis_id), analysis_result=mock_result, primary_language="Python")

    # 3. Trigger plan generation
    plan_resp = await client.post(
        f"/api/v1/repository-analyses/{analysis_id}/plan",
        headers=auth_headers,
    )
    assert plan_resp.status_code == 202
    plan_data = plan_resp.json()
    plan_id = plan_data["id"]
    assert plan_data["status"] == "PENDING"

    # 4. Fetch plan status
    status_resp = await client.get(
        f"/api/v1/infrastructure-plans/{plan_id}",
        headers=auth_headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == plan_id

    # 5. Fetch plan result
    result_resp = await client.get(
        f"/api/v1/infrastructure-plans/{plan_id}/result",
        headers=auth_headers,
    )
    assert result_resp.status_code == 200
    assert result_resp.json()["id"] == plan_id

    # 6. Test Regeneration
    regen_resp = await client.post(
        f"/api/v1/infrastructure-plans/{plan_id}/regenerate",
        headers=auth_headers,
    )
    assert regen_resp.status_code == 202
    assert regen_resp.json()["version"] == 2
