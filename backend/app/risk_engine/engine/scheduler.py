"""
Independent background evaluator for the Compound Risk Engine — deliberately NOT hooked into
the simulation engine's tick loop. Two reasons: (1) the simulator explicitly stands in for
real telemetry ingestion and must be swappable/disableable without silently taking risk
assessment down with it; (2) persistence is change-gated (see RiskService), so re-evaluating
every 5s simulation tick would mostly be wasted no-op work. Reads/writes the database
independently on its own interval, matching this codebase's established pattern of the DB as
the single source of truth between decoupled subsystems.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.repositories.risk import RiskRepository
from app.risk_engine.config.defaults import DEFAULT_RISK_CONFIG
from app.risk_engine.config.schema import RiskEngineConfig
from app.risk_engine.facts_builder import ZoneFactsBuilder
from app.services.risk import RiskService

logger = logging.getLogger(__name__)


class RiskScheduler:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        *,
        interval_seconds: float = 15.0,
        config: RiskEngineConfig = DEFAULT_RISK_CONFIG,
    ) -> None:
        self.session_factory = session_factory
        self.interval_seconds = interval_seconds
        self.config = config
        self._running = False

    async def run(self) -> None:
        logger.info("Risk scheduler started (evaluating every %.1fs)", self.interval_seconds)
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Risk evaluation pass failed")
            await asyncio.sleep(self.interval_seconds)

    async def run_once(self) -> None:
        # Guards against overlapping passes if a pass ever takes longer than interval_seconds.
        # An in-process flag, adequate for this single-process deployment (same assumption the
        # simulation engine already makes) — not safe for a multi-worker deployment.
        if self._running:
            logger.warning("Previous risk evaluation pass still running; skipping this cycle")
            return

        self._running = True
        try:
            async with self.session_factory() as session:
                builder = ZoneFactsBuilder(session)
                facts_by_zone = await builder.build_for_plant(self.config)
                service = RiskService(RiskRepository(session), builder, self.config)

                persisted = 0
                for facts in facts_by_zone.values():
                    if await service.evaluate_and_persist_if_changed(facts) is not None:
                        persisted += 1

                if persisted:
                    logger.info("Risk pass: %d zone snapshot(s) persisted", persisted)
        finally:
            self._running = False
