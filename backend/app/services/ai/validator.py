"""Validation layer for Infrastructure Plans — Schema + 10 Infrastructure Safety Rules."""
from __future__ import annotations

import json
import logging
from typing import Any
from pydantic import ValidationError

from app.services.ai.schemas import InfrastructurePlan

logger = logging.getLogger("cloudpilot.plan_validator")


class PlanValidator:
    """Validates raw LLM JSON responses against Pydantic schema and safety rules."""

    def validate(self, raw_json_str: str) -> tuple[bool, InfrastructurePlan | None, list[str]]:
        """
        Validates raw JSON string. Returns (is_valid, plan_object, list_of_error_strings).
        Applies deterministic auto-corrections for minor safety rule violations where safe.
        """
        errors: list[str] = []

        # 1. JSON Parsing & Pydantic Schema Validation
        try:
            raw_data = json.loads(raw_json_str)
        except json.JSONDecodeError as err:
            return False, None, [f"Invalid JSON string returned by LLM: {err}"]

        try:
            plan = InfrastructurePlan.model_validate(raw_data)
        except ValidationError as err:
            schema_errors = [f"Schema violation at {e['loc']}: {e['msg']}" for e in err.errors()]
            return False, None, schema_errors

        # 2. Rule Validation & Auto-Correction
        service_ids = {s.id.lower() for s in plan.services}
        public_ports: set[int] = set()

        # Check duplicate service IDs (Rule 5)
        if len(service_ids) != len(plan.services):
            errors.append("Rule 5 Violation: Duplicate service IDs detected in plan.")

        for svc in plan.services:
            svc_type = svc.type.lower()

            # Rule 1: Database/cache/queue CANNOT be public by default
            if svc_type in ("database", "cache", "queue", "storage") and svc.public:
                logger.warning(f"Rule 1 Auto-Correction: Setting public=False for private service '{svc.id}' ({svc_type})")
                svc.public = False

            # Rule 8: Only application/worker services can be horizontally scalable
            if svc_type in ("database", "cache", "storage") and (svc.scalable or svc.replicas.max > 1):
                logger.warning(f"Rule 8 Auto-Correction: Disabling horizontal scaling for {svc_type} '{svc.id}'")
                svc.scalable = False
                svc.replicas.min = 1
                svc.replicas.initial = 1
                svc.replicas.max = 1

            # Rule 2: Port range validation
            if svc.port is not None and not (1 <= svc.port <= 65535):
                errors.append(f"Rule 2 Violation: Service '{svc.id}' has invalid port number {svc.port}.")

            # Rule 3: Replica bounds
            if not (1 <= svc.replicas.min <= svc.replicas.initial <= svc.replicas.max <= 10):
                errors.append(
                    f"Rule 3 Violation: Service '{svc.id}' has invalid replica bounds "
                    f"(min={svc.replicas.min}, initial={svc.replicas.initial}, max={svc.replicas.max})."
                )

            # Rule 6: No public port conflicts
            if svc.public and svc.port is not None:
                if svc.port in public_ports:
                    errors.append(f"Rule 6 Violation: Public port conflict detected for port {svc.port}.")
                else:
                    public_ports.add(svc.port)

        # Rule 4: Dependency target validation
        for dep in plan.dependencies:
            if dep.source.lower() not in service_ids:
                errors.append(f"Rule 4 Violation: Dependency source '{dep.source}' does not exist in services.")
            if dep.target.lower() not in service_ids:
                errors.append(f"Rule 4 Violation: Dependency target '{dep.target}' does not exist in services.")

        # Rule 9: Volume attachment validation
        for vol in plan.volumes:
            if vol.service.lower() not in service_ids:
                errors.append(f"Rule 9 Violation: Volume '{vol.name}' attached to non-existent service '{vol.service}'.")

        # Rule 7: Secret literal check in environment
        for env_grp in plan.environment:
            for v in env_grp.variables:
                if v.secret and v.default and not v.default.startswith("${") and len(v.default) > 0:
                    logger.warning(f"Rule 7 Auto-Correction: Clearing literal secret default value for variable '{v.name}'")
                    v.default = None

        # Rule 10: Architecture Graph references check
        graph_node_ids = {n.id.lower() for n in plan.graph.nodes}
        for edge in plan.graph.edges:
            if edge.source.lower() not in service_ids:
                errors.append(f"Rule 10 Violation: Graph edge source '{edge.source}' not found in services.")
            if edge.target.lower() not in service_ids:
                errors.append(f"Rule 10 Violation: Graph edge target '{edge.target}' not found in services.")

        is_valid = len(errors) == 0
        return is_valid, plan if is_valid else None, errors
