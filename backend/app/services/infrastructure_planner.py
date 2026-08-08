"""
Infrastructure Planner Service — Phase 3 Stub.

This service will use the analysis result from the Repository Analyzer
to generate an infrastructure architecture:
- Select appropriate container resources (CPU, memory)
- Define service topology (web, worker, cache, database)
- Generate docker-compose / Kubernetes manifests
- Estimate resource costs

Implementation is deferred to Phase 3: AI Infrastructure Planner.
"""
from __future__ import annotations


class InfrastructurePlanner:
    """
    Generates an infrastructure plan from a repository analysis result.

    Phase 3 will implement:
    - LLM-powered architecture suggestion
    - Resource sizing based on detected framework
    - Service dependency graph generation
    - Manifest generation (docker-compose, Helm charts)
    """

    async def plan(self, analysis_result: dict, project_id: str) -> dict:
        """
        Generate an infrastructure plan.

        Args:
            analysis_result: Output from RepositoryAnalyzer.
            project_id: ID of the project being planned.

        Returns:
            InfrastructurePlan with services, resources, and manifests.

        Raises:
            NotImplementedError: Until Phase 3 is implemented.
        """
        raise NotImplementedError("Infrastructure planning is implemented in Phase 3.")
