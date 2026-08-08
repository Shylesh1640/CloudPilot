"""MetricsScheduler — background scheduler running periodic telemetry collection and retention cleanup."""
from __future__ import annotations

import asyncio
import logging
from app.core.database import AsyncSessionLocal
from app.repositories.observability_repository import ObservabilityRepository
from app.services.observability.collector import MetricsCollector
from app.services.observability.policies import DEFAULT_OBSERVABILITY_POLICY, ObservabilityPolicy

logger = logging.getLogger("cloudpilot.metrics_scheduler")


class MetricsScheduler:
    def __init__(self, policy: ObservabilityPolicy | None = None) -> None:
        self.policy = policy or DEFAULT_OBSERVABILITY_POLICY
        self.collector = MetricsCollector()
        self._task: asyncio.Task | None = None
        self._cleanup_counter = 0
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("MetricsScheduler background loop started.")

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("MetricsScheduler background loop stopped.")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self.collector.collect_and_store_cycle()
                self._cleanup_counter += 1

                # Every 120 cycles (~10 minutes), run 24-hour retention purge
                if self._cleanup_counter >= 120:
                    self._cleanup_counter = 0
                    async with AsyncSessionLocal() as session:
                        obs_repo = ObservabilityRepository(session)
                        purged = await obs_repo.purge_old_metrics(self.policy.telemetry_retention_hours)
                        if purged > 0:
                            logger.info(f"Purged {purged} telemetry records older than {self.policy.telemetry_retention_hours}h.")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception(f"Error in MetricsScheduler cycle: {exc}")

            await asyncio.sleep(self.policy.metrics_interval_seconds)
