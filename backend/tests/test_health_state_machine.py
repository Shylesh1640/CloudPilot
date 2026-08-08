"""Unit tests for threshold state machine, flapping detector, and dependency health rules."""
from __future__ import annotations

import pytest
from app.models.health import HealthStatus
from app.services.ai.schemas import InfrastructurePlan, ServiceDefinition, ServiceDependency
from app.services.health.dependency_checker import DependencyChecker
from app.services.health.deployment_health import DeploymentHealthManager
from app.services.health.flapping_detector import FlappingDetector
from app.services.health.policies import HealthPolicy


def test_flapping_detector_trigger():
    policy = HealthPolicy(flapping_window_seconds=300, flapping_threshold_switches=3)
    detector = FlappingDetector(policy)

    # 1. First state
    assert not detector.record_and_check_flapping("api", HealthStatus.HEALTHY)
    # 2. Switch 1
    assert not detector.record_and_check_flapping("api", HealthStatus.UNHEALTHY)
    # 3. Switch 2
    assert not detector.record_and_check_flapping("api", HealthStatus.HEALTHY)
    # 4. Switch 3 -> triggers flapping!
    assert detector.record_and_check_flapping("api", HealthStatus.UNHEALTHY)


def test_dependency_checker_required_vs_optional():
    plan = InfrastructurePlan(
        plan_version="1.0",
        analyzer_version="2.0",
        planner_version="1.0",
        application={"name": "app", "architecture_type": "multi_service"},
        services=[
            ServiceDefinition(id="api", name="API", type="application", runtime="python", port=8000, public=True),
            ServiceDefinition(id="postgres", name="Postgres", type="database", runtime="postgresql", port=5432, public=False),
            ServiceDefinition(id="redis", name="Redis", type="cache", runtime="redis", port=6379, public=False),
        ],
        networks=[],
        volumes=[],
        dependencies=[
            ServiceDependency(source="api", target="postgres", required=True),
            ServiceDependency(source="api", target="redis", required=False),
        ],
        environment=[],
        scaling=[],
        health_checks=[],
        resource_profiles=[],
        risks=[],
        graph={"nodes": [], "edges": []},
        explanation={"summary": "", "architecture_choice": "", "scaling_reasoning": "", "security_notes": ""},
        deployment_order=["postgres", "redis", "api"],
    )

    # Case A: Optional Redis fails -> DEGRADED
    health_map_opt_fail = {"postgres": HealthStatus.HEALTHY, "redis": HealthStatus.UNHEALTHY}
    res_opt = DependencyChecker.evaluate_dependencies("api", plan, health_map_opt_fail)
    assert res_opt is not None
    assert res_opt.status == HealthStatus.DEGRADED

    # Case B: Required Postgres fails -> FAILED
    health_map_req_fail = {"postgres": HealthStatus.FAILED, "redis": HealthStatus.HEALTHY}
    res_req = DependencyChecker.evaluate_dependencies("api", plan, health_map_req_fail)
    assert res_req is not None
    assert res_req.status == HealthStatus.FAILED


def test_deployment_health_manager_aggregation():
    plan = InfrastructurePlan(
        plan_version="1.0",
        analyzer_version="2.0",
        planner_version="1.0",
        application={"name": "app", "architecture_type": "multi_service"},
        services=[
            ServiceDefinition(id="api", name="API", type="application", runtime="python", port=8000, public=True),
            ServiceDefinition(id="redis", name="Redis", type="cache", runtime="redis", port=6379, public=False),
        ],
        networks=[],
        volumes=[],
        dependencies=[ServiceDependency(source="api", target="redis", required=False)],
        environment=[],
        scaling=[],
        health_checks=[],
        resource_profiles=[],
        risks=[],
        graph={"nodes": [], "edges": []},
        explanation={"summary": "", "architecture_choice": "", "scaling_reasoning": "", "security_notes": ""},
        deployment_order=["redis", "api"],
    )

    # All healthy -> HEALTHY
    assert DeploymentHealthManager.calculate_aggregate_health(
        {"api": HealthStatus.HEALTHY, "redis": HealthStatus.HEALTHY}, plan
    ) == HealthStatus.HEALTHY

    # Optional Redis unhealthy -> DEGRADED
    assert DeploymentHealthManager.calculate_aggregate_health(
        {"api": HealthStatus.HEALTHY, "redis": HealthStatus.UNHEALTHY}, plan
    ) == HealthStatus.DEGRADED

    # Public API unhealthy -> UNHEALTHY
    assert DeploymentHealthManager.calculate_aggregate_health(
        {"api": HealthStatus.UNHEALTHY, "redis": HealthStatus.HEALTHY}, plan
    ) == HealthStatus.UNHEALTHY
