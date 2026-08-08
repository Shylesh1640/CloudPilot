"""Integration tests for container orchestration API endpoints."""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient

from tests.conftest import TestSessionLocal
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.plan_repository import PlanRepository


@pytest.mark.asyncio
async def test_trigger_deployment_invalid_plan(client: AsyncClient, auth_headers: dict[str, str]):
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/infrastructure-plans/{fake_id}/deploy",
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_full_deployment_workflow(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "test-proj-deploy-api"},
        headers=auth_headers,
    )
    assert proj_resp.status_code == 201
    project_id = uuid.UUID(proj_resp.json()["id"])

    # 2. Setup mock analysis and plan in test DB
    mock_result = {
        "repository": {"owner": "example", "name": "fastapi-react", "url": "https://github.com/example/fastapi-react"},
        "languages": {"primary": "Python", "distribution": {"Python": 100.0}},
        "frameworks": [{"name": "FastAPI", "confidence": 0.98, "evidence": ["requirements.txt"]}],
        "dependencies": {"pip": ["fastapi", "uvicorn"]},
        "databases": [],
        "caches": [],
        "queues": [],
        "containers": {"detected": True, "has_dockerfile": True, "has_compose": False, "exposed_ports": [8000]},
        "ports": [{"port": 8000, "service": "api", "port_type": "application_port", "source": "Dockerfile"}],
        "environment_variables": [],
        "services": [{"name": "api", "type": "application", "runtime": "python", "port": 8000}],
        "is_monorepo": False,
        "monorepo_apps": [],
    }

    plan_data = {
        "plan_version": "1.0",
        "analyzer_version": "2.0",
        "planner_version": "1.0",
        "application": {"name": "fastapi-react", "architecture_type": "single_service"},
        "services": [
            {
                "id": "api",
                "name": "API",
                "type": "application",
                "runtime": "python",
                "port": 8000,
                "protocol": "http",
                "public": True,
                "replicas": {"min": 1, "initial": 1, "max": 1},
                "scalable": True,
                "confidence": 0.9,
                "evidence": ["Detected api"],
            }
        ],
        "networks": [{"name": "cloudpilot-internal", "type": "private"}],
        "volumes": [],
        "dependencies": [],
        "environment": [],
        "scaling": [],
        "health_checks": [],
        "resource_profiles": [],
        "risks": [],
        "graph": {
            "nodes": [{"id": "api", "label": "API", "type": "application", "public": True, "replicas": 1}],
            "edges": [],
        },
        "explanation": {
            "summary": "Deploy plan",
            "architecture_choice": "Single service",
            "scaling_reasoning": "Single instance",
            "security_notes": "Public API",
        },
        "deployment_order": ["api"],
    }

    async with TestSessionLocal() as session:
        anal_repo = AnalysisRepository(session)
        analysis = await anal_repo.create(
            project_id=project_id,
            repository_url="https://github.com/example/fastapi-react",
            repository_owner="example",
            repository_name="fastapi-react",
        )
        await anal_repo.save_result(analysis.id, analysis_result=mock_result, primary_language="Python")

        plan_repo = PlanRepository(session)
        plan_record = await plan_repo.create(project_id=project_id, repository_analysis_id=analysis.id)
        await plan_repo.save_result(
            plan_record.id,
            plan_data=plan_data,
            validation_result={"passed": True},
            duration_ms=100,
            ai_provider="mock",
            ai_model="gpt-4o-mini",
        )
        plan_id = plan_record.id

    # 3. Trigger Deployment
    deploy_resp = await client.post(
        f"/api/v1/infrastructure-plans/{plan_id}/deploy",
        headers=auth_headers,
    )
    assert deploy_resp.status_code == 202
    deployment_id = deploy_resp.json()["id"]

    # 4. Attempt second concurrent deployment -> should return 409 Conflict
    conflict_resp = await client.post(
        f"/api/v1/infrastructure-plans/{plan_id}/deploy",
        headers=auth_headers,
    )
    assert conflict_resp.status_code == 409

    # 5. Fetch deployment status
    status_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}",
        headers=auth_headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == deployment_id

    # 6. Fetch services list
    services_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/services",
        headers=auth_headers,
    )
    assert services_resp.status_code == 200

    # 7. Restart service (mocked container)
    restart_resp = await client.post(
        f"/api/v1/deployments/{deployment_id}/services/api/restart",
        headers=auth_headers,
    )
    assert restart_resp.status_code == 200

    # 8. Fetch service logs
    logs_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/services/api/logs",
        headers=auth_headers,
    )
    assert logs_resp.status_code == 200
    assert "logs" in logs_resp.json()

    # 9. Stop deployment
    stop_resp = await client.post(
        f"/api/v1/deployments/{deployment_id}/stop",
        headers=auth_headers,
    )
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "STOPPED"
