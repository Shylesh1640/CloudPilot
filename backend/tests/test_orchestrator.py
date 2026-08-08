"""Unit tests for Container Orchestrator modules."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock
import pytest

from app.services.ai.schemas import (
    ApplicationInfo,
    AIExplanation,
    InfrastructurePlan,
    NetworkDefinition,
    ServiceDefinition,
    VolumeDefinition,
)
from app.services.orchestrator import (
    ContainerManager,
    DependencyManager,
    DeploymentEngine,
    DockerRuntime,
    NetworkManager,
    VolumeManager,
)
from app.services.orchestrator.utils import make_container_name, make_network_name, make_volume_name


@pytest.fixture
def mock_runtime():
    runtime = MagicMock(spec=DockerRuntime)
    runtime.ping.return_value = True
    runtime.create_container.return_value = "mock-container-123"
    runtime.inspect_container.return_value = {"State": {"Status": "running", "Running": True}}
    runtime.get_container_logs.return_value = "Container started successfully."
    return runtime


@pytest.fixture
def sample_plan():
    return InfrastructurePlan(
        plan_version="1.0",
        analyzer_version="2.0",
        planner_version="1.0",
        application=ApplicationInfo(name="sample-app", architecture_type="multi_service"),
        services=[
            ServiceDefinition(
                id="api",
                name="API",
                type="application",
                port=8000,
                public=True,
                replicas={"min": 1, "initial": 1, "max": 2},
            ),
            ServiceDefinition(
                id="postgres",
                name="PostgreSQL",
                type="database",
                port=5432,
                public=False,
                replicas={"min": 1, "initial": 1, "max": 1},
            ),
        ],
        networks=[NetworkDefinition(name="cloudpilot-internal", type="private")],
        volumes=[VolumeDefinition(name="pg-data", service="postgres", persistent=True, mount_path="/var/lib/postgresql/data")],
        dependencies=[],
        environment=[],
        scaling=[],
        health_checks=[],
        resource_profiles=[],
        risks=[],
        explanation=AIExplanation(
            summary="Sample test plan",
            architecture_choice="Multi-service",
            scaling_reasoning="Baseline",
            security_notes="Private DB",
        ),
    )


def test_naming_utils():
    proj_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    net_name = make_network_name(proj_id)
    vol_name = make_volume_name(proj_id, "postgres")
    ctr_name = make_container_name(proj_id, "api", version=2)

    assert net_name == "cloudpilot-11111111-net"
    assert vol_name == "cloudpilot-11111111-postgres-data"
    assert ctr_name == "cloudpilot-11111111-api-v2"


def test_dependency_manager_order(sample_plan):
    order = DependencyManager.get_execution_order(sample_plan)
    # Databases must be ranked ahead of Application services
    assert order.index("postgres") < order.index("api")


def test_network_manager(mock_runtime):
    mgr = NetworkManager(mock_runtime)
    proj_id = uuid.uuid4()
    dep_id = uuid.uuid4()
    net_name = mgr.create_project_network(proj_id, dep_id)

    assert net_name.startswith("cloudpilot-")
    mock_runtime.create_network.assert_called_once()


def test_volume_manager(mock_runtime, sample_plan):
    mgr = VolumeManager(mock_runtime)
    proj_id = uuid.uuid4()
    dep_id = uuid.uuid4()
    vol_map = mgr.prepare_volumes(proj_id, dep_id, sample_plan.volumes)

    assert "postgres" in vol_map
    mock_runtime.create_volume.assert_called_once()


def test_container_manager_spec(mock_runtime, sample_plan):
    mgr = ContainerManager(mock_runtime)
    proj_id = uuid.uuid4()
    dep_id = uuid.uuid4()
    svc = sample_plan.services[0]  # api

    spec = mgr.prepare_container_spec(
        project_id=proj_id,
        deployment_id=dep_id,
        service=svc,
        image="cloudpilot/api:v1",
        network_name="test-net",
        plan=sample_plan,
        volume_map={},
    )

    assert spec.service_id == "api"
    assert spec.image == "cloudpilot/api:v1"
    assert "8000/tcp" in spec.ports
    assert spec.labels["cloudpilot.managed"] == "true"
