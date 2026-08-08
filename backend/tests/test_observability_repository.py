"""Unit tests for ObservabilityRepository time-series persistence and retention purging."""
from __future__ import annotations

import datetime
import uuid
import pytest
from tests.conftest import TestSessionLocal

from app.models.observability import ContainerMetricsModel
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.observability_repository import ObservabilityRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_observability_repository_purge():
    async with TestSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.create("obs_user@example.com", "Password123!")

        proj_repo = ProjectRepository(session)
        project = await proj_repo.create(user.id, name="obs-proj")

        anal_repo = AnalysisRepository(session)
        analysis = await anal_repo.create(
            project_id=project.id,
            repository_url="https://github.com/example/obs",
            repository_owner="example",
            repository_name="obs",
        )
        plan_repo = PlanRepository(session)
        plan = await plan_repo.create(project.id, analysis.id)

        dep_repo = DeploymentRepository(session)
        deployment = await dep_repo.create(project_id=project.id, infrastructure_plan_id=plan.id)

        obs_repo = ObservabilityRepository(session)

        # Insert fresh metric
        m_fresh = ContainerMetricsModel(
            project_id=project.id,
            deployment_id=deployment.id,
            service_id="api",
            container_id="c-fresh",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            cpu_percent=10.0,
            memory_usage_bytes=1000,
        )
        # Insert old metric (30 hours ago)
        old_ts = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=30)
        m_old = ContainerMetricsModel(
            project_id=project.id,
            deployment_id=deployment.id,
            service_id="api",
            container_id="c-old",
            timestamp=old_ts,
            cpu_percent=5.0,
            memory_usage_bytes=500,
        )
        await obs_repo.add_metrics_batch([m_fresh, m_old])

        # Purge metrics older than 24h
        purged = await obs_repo.purge_old_metrics(retention_hours=24)
        assert purged >= 1

        # Verify only fresh metric remains
        history = await obs_repo.get_service_history(deployment.id, "api")
        assert len(history) == 1
        assert history[0].container_id == "c-fresh"
