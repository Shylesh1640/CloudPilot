"""Restricted, cancellable traffic generator for managed deployment services only."""
from __future__ import annotations

import asyncio
import math
import uuid
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.models.autoscaling import TrafficRunModel
from app.repositories.autoscaling_repository import AutoscalingRepository


class TrafficController:
    def __init__(self, repository: AutoscalingRepository) -> None:
        self.repository = repository

    async def create(self, deployment, user_id: uuid.UUID, payload) -> TrafficRunModel:
        max_rps = max(v for v in (payload.requests_per_second, payload.start_rps, payload.end_rps, payload.baseline_rps, payload.spike_rps) if v is not None)
        if max_rps > settings.TRAFFIC_MAX_RPS:
            raise ValueError(f"RPS exceeds the configured maximum of {settings.TRAFFIC_MAX_RPS}.")
        if payload.duration_seconds > settings.TRAFFIC_MAX_DURATION_SECONDS:
            raise ValueError(f"Duration exceeds the configured maximum of {settings.TRAFFIC_MAX_DURATION_SECONDS} seconds.")
        if await self.repository.active_traffic_count(deployment.id) >= settings.TRAFFIC_MAX_CONCURRENT_RUNS:
            raise ValueError("Maximum concurrent traffic runs reached for this deployment.")
        config = payload.model_dump(exclude={"service_id", "scenario"})
        return await self.repository.create_traffic_run(TrafficRunModel(project_id=deployment.project_id, deployment_id=deployment.id, service_id=payload.service_id, scenario=payload.scenario, configuration=config, created_by=user_id))

    async def stop(self, run: TrafficRunModel) -> TrafficRunModel:
        if run.status in {"COMPLETED", "CANCELLED", "FAILED"}:
            return run
        return await self.repository.update_traffic_run(run, status="STOPPING")

    @staticmethod
    def rps_for(run: TrafficRunModel, elapsed: float) -> float:
        cfg, progress = run.configuration, min(1.0, elapsed / cfg["duration_seconds"])
        if run.scenario == "constant": return float(cfg["requests_per_second"])
        if run.scenario in {"ramp_up", "ramp_down"}: return float(cfg["start_rps"] + (cfg["end_rps"] - cfg["start_rps"]) * progress)
        # Spike occurs after a short warmup and is bounded by duration.
        return float(cfg["spike_rps"] if 5 <= elapsed < 5 + cfg["spike_duration_seconds"] else cfg["baseline_rps"])

    async def execute(self, run_id: uuid.UUID, target_base_url: str) -> None:
        run = await self.repository.get_traffic_run(run_id)
        if not run:
            return
        await self.repository.update_traffic_run(run, status="RUNNING")
        started = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                while (datetime.now(timezone.utc) - started).total_seconds() < run.configuration["duration_seconds"]:
                    await self.repository.session.refresh(run)
                    if run.status == "STOPPING":
                        await self.repository.update_traffic_run(run, status="CANCELLED", current_rps=0)
                        return
                    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                    rps = self.rps_for(run, elapsed)
                    await self.repository.update_traffic_run(run, current_rps=rps)
                    path = run.configuration.get("path", "/")
                    calls = [client.get(f"{target_base_url}{path}") for _ in range(min(math.ceil(rps), settings.TRAFFIC_MAX_RPS))]
                    if calls:
                        await asyncio.gather(*calls, return_exceptions=True)
                    await asyncio.sleep(1)
            await self.repository.update_traffic_run(run, status="COMPLETED", current_rps=0)
        except Exception:
            await self.repository.update_traffic_run(run, status="FAILED", current_rps=0)
