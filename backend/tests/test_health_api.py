"""Integration tests for Deployment & Health Engine API endpoints."""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient
from tests.conftest import TestSessionLocal

from app.models.deployment import DeploymentStatus
from app.models.health import HealthStatus
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.health_repository import HealthRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.analysis_repository import AnalysisRepository


@pytest.mark.asyncio
async def test_health_api_workflow(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "test-proj-health-api"},
        headers=auth_headers,
    )
    assert proj_resp.status_code == 201
    project_id = uuid.UUID(proj_resp.json()["id"])

    # 2. Setup mock analysis, plan, deployment, and service in test DB
    mock_result = {
        "repository": {"owner": "example", "name": "app", "url": "https://github.com/example/app"},
        "languages": {"primary": "Python", "distribution": {"Python": 100.0}},
        "frameworks": [],
        "dependencies": {},
        "databases": [],
        "caches": [],
        "queues": [],
        "containers": {"detected": True},
        "ports": [],
        "environment_variables": [],
        "services": [{"name": "api", "type": "application", "runtime": "python", "port": 8000}],
        "is_monorepo": False,
        "monorepo_apps": [],
    }

    plan_data = {
        "plan_version": "1.0",
        "analyzer_version": "2.0",
        "planner_version": "1.0",
        "application": {"name": "app", "architecture_type": "single_service"},
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
                "evidence": [],
            }
        ],
        "networks": [],
        "volumes": [],
        "dependencies": [],
        "environment": [],
        "scaling": [],
        "health_checks": [],
        "resource_profiles": [],
        "risks": [],
        "graph": {"nodes": [{"id": "api", "label": "API", "type": "application", "public": True, "replicas": 1}], "edges": []},
        "explanation": {"summary": "", "architecture_choice": "", "scaling_reasoning": "", "security_notes": ""},
        "deployment_order": ["api"],
    }

    async with TestSessionLocal() as session:
        anal_repo = AnalysisRepository(session)
        analysis = await anal_repo.create(
            project_id=project_id,
            repository_url="https://github.com/example/app",
            repository_owner="example",
            repository_name="app",
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

        dep_repo = DeploymentRepository(session)
        deployment = await dep_repo.create(project_id=project_id, infrastructure_plan_id=plan_record.id)
        svc_model = await dep_repo.add_service(
            deployment_id=deployment.id,
            service_id="api",
            container_name="cloudpilot-test-api",
            image="cloudpilot/test/api:v1",
            port=8000,
            public=True,
        )

        # Update service health
        health_repo = HealthRepository(session)
        await health_repo.update_service_health(
            svc_model.id,
            status=HealthStatus.HEALTHY,
            consecutive_failures=0,
            consecutive_successes=5,
            latency_ms=42,
        )
        # Add check record
        await health_repo.add_check_record(
            deployment_service_id=svc_model.id,
            check_type="HTTP",
            status=HealthStatus.HEALTHY,
            latency_ms=42,
            status_code=200,
        )
        # Add health event
        await health_repo.record_event(
            project_id=project_id,
            deployment_id=deployment.id,
            service_id="api",
            event_type="SERVICE_HEALTHY",
            previous_state="STARTING",
            new_state="HEALTHY",
            message="Service api passed health check.",
        )

        deployment_id = deployment.id

    # 3. GET /deployments/{id}/health
    health_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/health",
        headers=auth_headers,
    )
    assert health_resp.status_code == 200
    h_json = health_resp.json()
    assert h_json["status"] == "HEALTHY"
    assert h_json["services"]["api"] == "HEALTHY"

    # 4. GET /deployments/{id}/services/api/health
    svc_health_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/services/api/health",
        headers=auth_headers,
    )
    assert svc_health_resp.status_code == 200
    assert svc_health_resp.json()["status"] == "HEALTHY"

    # 5. GET /deployments/{id}/services/api/health/history
    hist_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/services/api/health/history",
        headers=auth_headers,
    )
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 1

    # 6. GET /deployments/{id}/health/events
    events_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/health/events",
        headers=auth_headers,
    )
    assert events_resp.status_code == 200
    assert len(events_resp.json()) >= 1
    assert events_resp.json()[0]["event_type"] == "SERVICE_HEALTHY"
