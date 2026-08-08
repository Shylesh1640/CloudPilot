"""Unit tests for PlanValidator schema enforcement and 10 Infrastructure Safety Rules."""
from __future__ import annotations

import json
import pytest

from app.services.ai import PlanValidator


@pytest.fixture
def base_valid_plan_dict():
    return {
        "plan_version": "1.0",
        "analyzer_version": "2.0",
        "planner_version": "1.0",
        "application": {"name": "test-app", "architecture_type": "multi_service"},
        "services": [
            {
                "id": "frontend",
                "name": "Frontend",
                "type": "application",
                "runtime": "node",
                "port": 5173,
                "public": True,
                "replicas": {"min": 1, "initial": 1, "max": 5},
                "scalable": True,
            },
            {
                "id": "postgres",
                "name": "PostgreSQL",
                "type": "database",
                "port": 5432,
                "public": False,
                "replicas": {"min": 1, "initial": 1, "max": 1},
                "scalable": False,
            },
        ],
        "networks": [{"name": "cloudpilot-internal", "type": "private"}],
        "volumes": [{"name": "pg-data", "service": "postgres", "persistent": True}],
        "dependencies": [{"source": "frontend", "target": "postgres", "dependency_type": "database"}],
        "environment": [],
        "scaling": [],
        "health_checks": [],
        "resource_profiles": [],
        "risks": [],
        "graph": {
            "nodes": [
                {"id": "frontend", "label": "Frontend", "type": "application", "public": True},
                {"id": "postgres", "label": "PostgreSQL", "type": "database", "public": False},
            ],
            "edges": [{"source": "frontend", "target": "postgres", "label": "queries"}],
        },
        "explanation": {
            "summary": "Valid test plan.",
            "architecture_choice": "Multi-service",
            "scaling_reasoning": "Frontend scales",
            "security_notes": "DB private",
        },
        "deployment_order": ["postgres", "frontend"],
    }


def test_valid_plan_passes(base_valid_plan_dict):
    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))
    assert is_valid is True
    assert plan is not None
    assert len(errors) == 0


def test_rule_1_public_database_auto_corrected(base_valid_plan_dict):
    # Set public = True on PostgreSQL database
    base_valid_plan_dict["services"][1]["public"] = True
    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))

    assert is_valid is True
    assert plan is not None
    # Rule 1 auto-corrects public to False
    assert plan.services[1].public is False


def test_rule_8_database_scaling_auto_corrected(base_valid_plan_dict):
    # Set scalable = True and max = 5 on database
    base_valid_plan_dict["services"][1]["scalable"] = True
    base_valid_plan_dict["services"][1]["replicas"]["max"] = 5

    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))

    assert is_valid is True
    assert plan is not None
    # Rule 8 auto-corrects scaling to False and max to 1
    assert plan.services[1].scalable is False
    assert plan.services[1].replicas.max == 1


def test_rule_2_invalid_port_range(base_valid_plan_dict):
    base_valid_plan_dict["services"][0]["port"] = 999999
    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))

    assert is_valid is False
    assert any("Schema violation" in e or "Rule 2" in e for e in errors)


def test_rule_3_invalid_replica_bounds(base_valid_plan_dict):
    # min > max
    base_valid_plan_dict["services"][0]["replicas"] = {"min": 5, "initial": 2, "max": 1}
    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))

    assert is_valid is False
    assert any("Rule 3" in e for e in errors)


def test_rule_4_invalid_dependency_target(base_valid_plan_dict):
    base_valid_plan_dict["dependencies"].append({"source": "frontend", "target": "non-existent-db"})
    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))

    assert is_valid is False
    assert any("Rule 4" in e for e in errors)


def test_rule_6_public_port_conflict(base_valid_plan_dict):
    # Add second public service on port 5173
    base_valid_plan_dict["services"].append({
        "id": "admin-ui",
        "name": "Admin",
        "type": "application",
        "port": 5173,
        "public": True,
        "replicas": {"min": 1, "initial": 1, "max": 1},
    })
    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))

    assert is_valid is False
    assert any("Rule 6" in e for e in errors)


def test_rule_9_invalid_volume_attachment(base_valid_plan_dict):
    base_valid_plan_dict["volumes"].append({"name": "bad-vol", "service": "ghost-service", "persistent": True})
    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))

    assert is_valid is False
    assert any("Rule 9" in e for e in errors)


def test_rule_10_invalid_graph_edge(base_valid_plan_dict):
    base_valid_plan_dict["graph"]["edges"].append({"source": "frontend", "target": "missing-node"})
    validator = PlanValidator()
    is_valid, plan, errors = validator.validate(json.dumps(base_valid_plan_dict))

    assert is_valid is False
    assert any("Rule 10" in e for e in errors)
