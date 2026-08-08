"""Integration tests for Observability API endpoints and WebSocket authorization."""
from __future__ import annotations

import datetime
import uuid
import pytest
from httpx import AsyncClient
from tests.conftest import TestSessionLocal

from app.models.observability import ContainerMetricsModel
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.observability_repository import ObservabilityRepository
from app.repositories.plan_repository import PlanRepository


@pytest.mark.asyncio
async def test_observability_api_endpoints(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "test-proj-obs-api"},
        headers=auth_headers,
    )
    assert proj_resp.status_code == 201
    project_id = uuid.UUID(proj_resp.json()["id"])

    # 2. Setup mock DB data
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

        # Insert telemetry record
        obs_repo = ObservabilityRepository(session)
        await obs_repo.add_metrics(
            ContainerMetricsModel(
                project_id=project_id,
                deployment_id=deployment.id,
                service_id="api",
                container_id="cloudpilot-test-api",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                cpu_percent=42.5,
                memory_usage_bytes=150 * 1024 * 1024,
                memory_percent=30.0,
                network_rx_rate=1024.0,
                network_tx_rate=2048.0,
                restart_count=0,
                container_state="running",
            )
        )
        deployment_id = deployment.id

    # 3. GET /deployments/{id}/metrics
    metrics_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/metrics",
        headers=auth_headers,
    )
    assert metrics_resp.status_code == 200
    m_json = metrics_resp.json()
    assert "services" in m_json
    assert "api" in m_json["services"]
    assert m_json["services"]["api"]["cpu_percent"] == 42.5

    # 4. GET /deployments/{id}/services/api/metrics/current
    curr_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/services/api/metrics/current",
        headers=auth_headers,
    )
    assert curr_resp.status_code == 200
    assert curr_resp.json()["cpu_percent"] == 42.5

    # 5. GET /deployments/{id}/services/api/metrics
    hist_resp = await client.get(
        f"/api/v1/deployments/{deployment_id}/services/api/metrics?minutes=15",
        headers=auth_headers,
    )
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 1
